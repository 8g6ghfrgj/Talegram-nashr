import asyncio
import logging
import random

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

logger = logging.getLogger(__name__)


# =========================
# TELEGRAM MANAGER
# =========================

class TelegramBotManager:

    def __init__(self, db):
        self.db = db

        # admin_id -> asyncio.Task
        self.publish_tasks = {}

        # session_string -> TelegramClient
        self.clients = {}

        # default delay (seconds)
        self.publish_delay = 1.0  # ثانية واحدة بين كل رسالة
        
        # cache للمجموعات
        self.groups_cache = {}
        
        # قفل للمزامنة
        self._lock = asyncio.Lock()


    # ==================================================
    # CLIENT HANDLING (بدون API_ID و API_HASH)
    # ==================================================

    async def get_client(self, session_string: str) -> TelegramClient:
        """إنشاء عميل Telethon من StringSession كامل"""

        async with self._lock:
            if session_string in self.clients:
                return self.clients[session_string]

            # إنشاء عميل باستخدام StringSession فقط - لا حاجة لـ API_ID و API_HASH
            client = TelegramClient(
                StringSession(session_string),
                1,  # رقم وهمي - لن يُستخدم لأن StringSession مكتمل
                "dummy"  # نص وهمي - لن يُستخدم لأن StringSession مكتمل
            )

            await client.connect()

            if not await client.is_user_authorized():
                raise RuntimeError("Session not authorized - الجلسة غير صالحة")

            self.clients[session_string] = client
            logger.info("✅ Client connected successfully")
            return client


    # ==================================================
    # FETCH ALL GROUPS FROM ACCOUNT
    # ==================================================

    async def fetch_all_groups(self, session_string: str) -> list:
        """جلب جميع المجموعات التي فيها الحساب"""
        
        if session_string in self.groups_cache:
            return self.groups_cache[session_string]
        
        try:
            client = await self.get_client(session_string)
            groups = []
            
            logger.info("Fetching all groups from account...")
            
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    username = getattr(dialog.entity, "username", None)
                    group_info = {
                        'id': dialog.id,
                        'name': dialog.name,
                        'username': username,
                        'link': f"https://t.me/{username}" if username else None,
                        'chat_id': dialog.entity.id,
                    }
                    groups.append(group_info)
            
            self.groups_cache[session_string] = groups
            logger.info(f"✅ Found {len(groups)} groups in account")
            
            return groups
            
        except Exception as e:
            logger.error(f"Error fetching groups: {e}")
            return []


    # ==================================================
    # SEND MESSAGE TO SINGLE GROUP
    # ==================================================

    async def send_to_group(self, client, target, ad_type, ad_text, ad_media, group_name, account_id):
        """إرسال رسالة إلى مجموعة واحدة"""
        try:
            if ad_type == "text":
                await client.send_message(target, ad_text)
            elif ad_type == "photo":
                if ad_media:
                    await client.send_file(target, ad_media, caption=ad_text)
                else:
                    await client.send_message(target, ad_text)
            elif ad_type == "contact":
                if ad_media:
                    await client.send_file(target, ad_media)
                else:
                    await client.send_message(target, ad_text)
            else:
                await client.send_message(target, ad_text)
            
            logger.info(f"[SENT] ✅ Account {account_id} -> {group_name}")
            return True
            
        except FloodWaitError as e:
            logger.warning(f"[FLOODWAIT] {e.seconds}s")
            await asyncio.sleep(min(e.seconds, 60))
            return False
        except Exception as e:
            logger.error(f"[ERROR] {e}")
            return False


    # ==================================================
    # PUBLISH FROM ONE ACCOUNT
    # ==================================================

    async def publish_from_account(self, acc, ads, admin_id):
        """نشر من حساب واحد"""
        
        session_string = acc['session']
        
        groups = await self.fetch_all_groups(session_string)
        
        if not groups:
            logger.warning(f"No groups for account {acc['id']}")
            return 0
        
        logger.info(f"📊 Account {acc['id']} publishing to {len(groups)} groups")
        
        try:
            client = await self.get_client(session_string)
        except Exception as e:
            logger.error(f"Client error: {e}")
            return 0
        
        sent_count = 0
        
        for ad in ads:
            ad_type = ad['type']
            ad_text = ad['text'] or ""
            ad_media = ad.get('media_path', None)
            
            tasks = []
            for group in groups:
                if group['username']:
                    target = f"@{group['username']}"
                else:
                    target = group['chat_id']
                
                task = self.send_to_group(
                    client, target, ad_type, ad_text, ad_media, 
                    group['name'], acc['id']
                )
                tasks.append(task)
                
                if len(tasks) >= 50:
                    results = await asyncio.gather(*tasks)
                    sent_count += sum(results)
                    tasks = []
                    await asyncio.sleep(self.publish_delay)
            
            if tasks:
                results = await asyncio.gather(*tasks)
                sent_count += sum(results)
        
        return sent_count


    # ==================================================
    # MAIN PUBLISH LOOP
    # ==================================================

    async def _publish_loop(self, admin_id: int):

        logger.info(f"[PUBLISH LOOP STARTED] for admin {admin_id}")
        
        try:
            while True:

                accounts = self.db.get_accounts(admin_id)
                ads = self.db.get_ads(admin_id)
                
                active_accounts = [a for a in accounts if a['active'] == 1]
                active_ads = []
                for ad in ads:
                    try:
                        if 'active' in ad.keys():
                            if ad['active'] == 1:
                                active_ads.append(ad)
                        else:
                            active_ads.append(ad)
                    except:
                        active_ads.append(ad)
                
                if not active_accounts:
                    logger.warning("No active accounts")
                    await asyncio.sleep(10)
                    continue
                    
                if not active_ads:
                    logger.warning("No active ads")
                    await asyncio.sleep(10)
                    continue
                
                logger.info(f"🚀 Starting parallel publishing with {len(active_accounts)} accounts")
                
                account_tasks = []
                for acc in active_accounts:
                    task = self.publish_from_account(acc, active_ads, admin_id)
                    account_tasks.append(task)
                
                results = await asyncio.gather(*account_tasks)
                total_sent = sum(results)
                
                logger.info(f"✅ Cycle completed: {total_sent} messages sent")
                
                self.groups_cache.clear()
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            logger.info(f"[PUBLISH LOOP CANCELLED] admin {admin_id}")
        except Exception as e:
            logger.exception(f"[PUBLISH LOOP ERROR] {e}")


    # ==================================================
    # START / STOP PUBLISHING
    # ==================================================

    def start_publishing(self, admin_id: int) -> bool:
        if admin_id in self.publish_tasks:
            return False
        
        task = asyncio.create_task(self._publish_loop(admin_id))
        self.publish_tasks[admin_id] = task
        logger.info(f"[PUBLISH] Started for admin {admin_id}")
        return True


    def stop_publishing(self, admin_id: int) -> bool:
        task = self.publish_tasks.pop(admin_id, None)
        if not task:
            return False
        task.cancel()
        logger.info(f"[PUBLISH] Stopped for admin {admin_id}")
        return True


    # ==================================================
    # TEST PUBLISH
    # ==================================================

    async def test_publish_once(self, update, context):
        """اختبار سريع"""
        
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        active_accounts = [a for a in accounts if a['active'] == 1]
        
        if not active_accounts:
            await update.message.reply_text("❌ لا يوجد حسابات مفعلة")
            return
        
        await update.message.reply_text("⚡ جاري الاختبار...")
        
        total_sent = 0
        
        for acc in active_accounts:
            groups = await self.fetch_all_groups(acc['session'])
            
            if not groups:
                continue
            
            try:
                client = await self.get_client(acc['session'])
                
                for group in groups[:5]:
                    target = f"@{group['username']}" if group['username'] else group['chat_id']
                    try:
                        await client.send_message(target, "⚡ اختبار - البوت يعمل بكفاءة!")
                        total_sent += 1
                    except:
                        pass
            except:
                continue
        
        await update.message.reply_text(f"✅ تم الإرسال إلى {total_sent} مجموعة!")


    # ==================================================
    # SHOW ALL GROUPS
    # ==================================================

    async def show_all_groups(self, update, context):
        """عرض جميع المجموعات"""
        
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        active_accounts = [a for a in accounts if a['active'] == 1]
        
        if not active_accounts:
            await update.message.reply_text("❌ لا يوجد حسابات مفعلة")
            return
        
        await update.message.reply_text("⏳ جاري جلب المجموعات...")
        
        result = "📋 **جميع المجموعات:**\n\n"
        total = 0
        
        for acc in active_accounts:
            groups = await self.fetch_all_groups(acc['session'])
            total += len(groups)
            result += f"👤 حساب {acc['id']}: {len(groups)} مجموعة\n"
        
        result += f"\n📊 **الإجمالي: {total} مجموعة**"
        await update.message.reply_text(result, parse_mode='Markdown')


    # ==================================================
    # STATUS
    # ==================================================

    async def get_status(self, update, context):
        """حالة البوت"""
        
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        ads = self.db.get_ads(admin_id)
        
        active_accounts = [a for a in accounts if a['active'] == 1]
        is_publishing = admin_id in self.publish_tasks
        
        status_text = f"""
⚡ **حالة البوت**
━━━━━━━━━━━━━━━━━━━
🚀 النشر: {'✅ شغال' if is_publishing else '⭕ متوقف'}
👥 الحسابات: {len(accounts)} (مفعل: {len(active_accounts)})
📢 الإعلانات: {len(ads)}
⏱ التأخير: {self.publish_delay} ثانية
━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(status_text, parse_mode='Markdown')


    # ==================================================
    # CLEANUP
    # ==================================================

    async def shutdown(self):
        for task in self.publish_tasks.values():
            task.cancel()
        for client in self.clients.values():
            await client.disconnect()
        self.publish_tasks.clear()
        self.clients.clear()
        self.groups_cache.clear()
