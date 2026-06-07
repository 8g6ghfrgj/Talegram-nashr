import asyncio
import logging
import random
from typing import List, Dict, Any

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

logger = logging.getLogger(__name__)

# =========================
# TELETHON CREDENTIALS
# =========================
API_ID = 36658136
API_HASH = "b06f6af26c3938d019af883d38d3c103"

class TelegramBotManager:
    def __init__(self, db):
        self.db = db
        self.publish_tasks = {}      # admin_id -> asyncio.Task
        self.clients = {}            # session_string -> TelegramClient
        self.publish_delay = 5.0     # seconds between messages (per account)
        self.groups_cache = {}       # session_string -> list of groups
        self.semaphore_per_account = {}  # session_string -> Semaphore(concurrent_limit)
        self.CONCURRENT_LIMIT = 5    # عدد الرسائل المتزامنة لكل حساب (تجنب الفلوود)

    # ------------------------------
    # CLIENT HANDLING (مثل ما هو مع تحسين بسيط)
    # ------------------------------
    async def get_client(self, session_string: str) -> TelegramClient:
        if not session_string or not isinstance(session_string, str):
            raise ValueError("Invalid session_string")
        if session_string in self.clients:
            client = self.clients[session_string]
            if client.is_connected():
                return client
            else:
                await client.connect()
                if await client.is_user_authorized():
                    return client
                else:
                    del self.clients[session_string]
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("Session not authorized")
        self.clients[session_string] = client
        self.semaphore_per_account[session_string] = asyncio.Semaphore(self.CONCURRENT_LIMIT)
        return client

    # ------------------------------
    # FETCH GROUPS (مثل ما هو)
    # ------------------------------
    async def fetch_all_groups(self, session_string: str) -> list:
        if not session_string:
            return []
        if session_string in self.groups_cache:
            return self.groups_cache[session_string]
        try:
            client = await self.get_client(session_string)
            groups = []
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    groups.append({
                        'id': dialog.id,
                        'name': str(dialog.name),
                        'title': str(dialog.title or dialog.name),
                        'username': getattr(dialog.entity, 'username', None),
                        'link': f"https://t.me/{dialog.entity.username}" if getattr(dialog.entity, 'username', None) else None,
                        'chat_id': dialog.entity.id,
                        'is_group': dialog.is_group,
                        'is_channel': dialog.is_channel,
                    })
            self.groups_cache[session_string] = groups
            logger.info(f"Fetched {len(groups)} groups for session")
            return groups
        except Exception as e:
            logger.error(f"fetch_all_groups error: {e}")
            return []

    def clear_cache(self):
        self.groups_cache.clear()

    # ------------------------------
    # START / STOP PUBLISHING
    # ------------------------------
    def start_publishing(self, admin_id: int) -> bool:
        if admin_id in self.publish_tasks:
            return False
        task = asyncio.create_task(self._publish_loop(admin_id))
        self.publish_tasks[admin_id] = task
        logger.info(f"Publishing started for admin {admin_id}")
        return True

    def stop_publishing(self, admin_id: int) -> bool:
        task = self.publish_tasks.pop(admin_id, None)
        if task:
            task.cancel()
            logger.info(f"Publishing stopped for admin {admin_id}")
            return True
        return False

    # ------------------------------
    # NEW: PARALLEL SENDER WITH SEMAPHORE
    # ------------------------------
    async def _send_to_group(self, client: TelegramClient, group: dict, ad: dict, account_id: int, semaphore: asyncio.Semaphore):
        """إرسال رسالة إلى مجموعة واحدة مع التحكم في التزامن"""
        async with semaphore:
            try:
                target = f"@{group['username']}" if group.get('username') else group['chat_id']
                ad_type = ad.get('type', 'text')
                ad_text = ad.get('text', '')
                ad_media = ad.get('media_path')

                if ad_type == "text":
                    await client.send_message(target, ad_text)
                elif ad_type == "photo" and ad_media:
                    await client.send_file(target, ad_media, caption=ad_text)
                else:
                    await client.send_message(target, ad_text)

                logger.info(f"✅ Sent to {group['name']} (account {account_id})")
                await asyncio.sleep(self.publish_delay)  # ننتظر بين الرسائل لنفس الحساب
                return True
            except FloodWaitError as e:
                logger.warning(f"FloodWait {e.seconds}s on {group['name']}")
                await asyncio.sleep(e.seconds)
                return False
            except Exception as e:
                logger.error(f"Send error to {group['name']}: {e}")
                await asyncio.sleep(1)
                return False

    async def _publish_for_account(self, account: dict, ads: List[dict], admin_id: int):
        """نشر جميع الإعلانات النشطة إلى جميع مجموعات هذا الحساب بشكل متوازي"""
        session_string = account.get('session')
        if not session_string:
            return 0, 0

        groups = await self.fetch_all_groups(session_string)
        if not groups:
            logger.warning(f"No groups for account {account['id']}")
            return 0, 0

        # الحصول على السيمافور الخاص بهذا الحساب
        semaphore = self.semaphore_per_account.get(session_string)
        if not semaphore:
            # تأكد من وجود client لإنشاء السيمافور
            try:
                await self.get_client(session_string)
                semaphore = self.semaphore_per_account[session_string]
            except:
                return 0, 0

        total_sent = 0
        # لكل إعلان نرسله إلى كل المجموعات بالتوازي (مع السيمافور)
        for ad in ads:
            if ad.get('active') != 1:
                continue
            # إنشاء مهمة لكل مجموعة
            tasks = []
            for group in groups:
                tasks.append(self._send_to_group(
                    client=await self.get_client(session_string),  # client سيتم استرجاعه من الكاش
                    group=group,
                    ad=ad,
                    account_id=account['id'],
                    semaphore=semaphore
                ))
            # تنفيذ جميع المهام بالتوازي (لكن السيمافور سيحدد العدد المتزامن)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sent = sum(1 for r in results if r is True)
            total_sent += sent
            logger.info(f"Account {account['id']}: sent {sent}/{len(groups)} for ad {ad['id']}")
        return total_sent, len(groups) * len([a for a in ads if a.get('active')==1])

    # ------------------------------
    # MAIN PUBLISH LOOP (محسّن بالتوازي)
    # ------------------------------
    async def _publish_loop(self, admin_id: int):
        logger.info(f"Publish loop started for admin {admin_id}")
        try:
            while True:
                accounts = self.db.get_accounts(admin_id)
                ads = self.db.get_ads(admin_id)

                active_accounts = [a for a in accounts if a.get('active') == 1 and a.get('session')]
                active_ads = [ad for ad in ads if ad.get('active') == 1]

                if not active_accounts or not active_ads:
                    logger.warning("No active accounts or ads, waiting 30s")
                    await asyncio.sleep(30)
                    continue

                # إنشاء مهمة لكل حساب (تنفيذ متوازي عبر الحسابات)
                account_tasks = []
                for acc in active_accounts:
                    account_tasks.append(self._publish_for_account(acc, active_ads, admin_id))

                # انتظر حتى تنتهي جميع الحسابات من نشر جميع الإعلانات إلى جميع المجموعات
                results = await asyncio.gather(*account_tasks, return_exceptions=True)

                total_sent = 0
                total_possible = 0
                for r in results:
                    if isinstance(r, tuple):
                        total_sent += r[0]
                        total_possible += r[1]
                logger.info(f"Cycle completed: {total_sent}/{total_possible} messages sent")

                # تحديث الكاش (لجلب مجموعات جديدة) كل دورة
                self.groups_cache.clear()
                await asyncio.sleep(60)  # انتظر دقيقة قبل الدورة التالية

        except asyncio.CancelledError:
            logger.info(f"Publish loop cancelled for admin {admin_id}")
        except Exception as e:
            logger.exception(f"Publish loop error: {e}")

    # ------------------------------
    # COMMANDS FOR PUBLISHING CONTROL
    # ------------------------------
    async def start_publish_command(self, update, context):
        admin_id = update.effective_user.id
        if not self.db.is_admin(admin_id):
            await update.message.reply_text("❌ غير مصرح")
            return
        if self.start_publishing(admin_id):
            await update.message.reply_text("✅ تم بدء النشر التلقائي السريع في جميع المجموعات لجميع الحسابات!")
        else:
            await update.message.reply_text("⚠️ النشر يعمل بالفعل")

    async def stop_publish_command(self, update, context):
        admin_id = update.effective_user.id
        if self.stop_publishing(admin_id):
            await update.message.reply_text("⏹ تم إيقاف النشر التلقائي")
        else:
            await update.message.reply_text("⚠️ لا يوجد نشر نشط")

    async def set_delay_command(self, update, context):
        admin_id = update.effective_user.id
        if not self.db.is_admin(admin_id):
            return
        try:
            new_delay = float(context.args[0])
            if new_delay < 0.5:
                await update.message.reply_text("⚠️ التأخير لا يمكن أن يقل عن 0.5 ثانية")
                return
            self.publish_delay = new_delay
            await update.message.reply_text(f"✅ تم ضبط التأخير إلى {new_delay} ثانية بين الرسائل")
        except:
            await update.message.reply_text("استخدم: /set_delay <ثواني>")

    # ------------------------------
    # TEST & STATUS (مثل ما هو)
    # ------------------------------
    async def test_publish_once(self, update, context):
        # يمكنك الاحتفاظ بالكود القديم أو تحسينه
        await update.message.reply_text("🧪 وضع التجربة: سيتم الإرسال لأول 3 مجموعات فقط (موازي)")
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        active_accounts = [a for a in accounts if a.get('active') == 1 and a.get('session')]
        if not active_accounts:
            await update.message.reply_text("❌ لا توجد حسابات")
            return
        for acc in active_accounts:
            groups = await self.fetch_all_groups(acc['session'])
            if not groups:
                continue
            client = await self.get_client(acc['session'])
            sem = asyncio.Semaphore(3)
            tasks = []
            for group in groups[:3]:
                ad = {'type':'text', 'text':'🧪 رسالة تجربة سريعة من البوت ✅'}
                tasks.append(self._send_to_group(client, group, ad, acc['id'], sem))
            await asyncio.gather(*tasks)
        await update.message.reply_text("✅ تم إرسال رسائل التجربة")

    async def show_all_groups(self, update, context):
        # نفس الكود القديم
        pass

    async def get_status(self, update, context):
        admin_id = update.effective_user.id
        is_pub = admin_id in self.publish_tasks
        accounts = self.db.get_accounts(admin_id)
        active = [a for a in accounts if a.get('active')]
        text = f"🚀 النشر: {'شغال' if is_pub else 'متوقف'}\n👥 الحسابات: {len(accounts)}\n✅ المفعلة: {len(active)}\n⏱ التأخير: {self.publish_delay} ثانية\n⚡ التزامن: {self.CONCURRENT_LIMIT} رسالة/حساب"
        await update.message.reply_text(text)

    async def shutdown(self):
        for t in self.publish_tasks.values():
            t.cancel()
        for c in self.clients.values():
            await c.disconnect()
