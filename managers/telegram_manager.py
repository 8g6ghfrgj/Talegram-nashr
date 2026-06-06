import asyncio
import logging
import random

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

logger = logging.getLogger(__name__)


# =========================
# TELETHON CREDENTIALS
# =========================

API_ID = 36658136        # ضع api_id الحقيقي من my.telegram.org
API_HASH = "b06f6af26c3938d019af883d38d3c103"  # ضع api_hash الحقيقي من my.telegram.org


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
        self.publish_delay = 5.0  # 5 ثواني بين كل رسالة
        
        # cache للمجموعات (session_string -> list of groups)
        self.groups_cache = {}


    # ==================================================
    # CLIENT HANDLING
    # ==================================================

    async def get_client(self, session_string: str) -> TelegramClient:

        if session_string in self.clients:
            return self.clients[session_string]

        client = TelegramClient(
            StringSession(session_string),
            API_ID,
            API_HASH
        )

        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError("Session not authorized")

        self.clients[session_string] = client
        return client


    # ==================================================
    # FETCH ALL GROUPS FROM ACCOUNT
    # ==================================================

    async def fetch_all_groups(self, session_string: str) -> list:
        """جلب جميع المجموعات التي فيها الحساب"""
        
        # تحقق من الكاش أولاً
        if session_string in self.groups_cache:
            logger.info(f"Using cached groups for session")
            return self.groups_cache[session_string]
        
        try:
            client = await self.get_client(session_string)
            groups = []
            
            logger.info("Fetching all groups from account...")
            
            async for dialog in client.iter_dialogs():
                # جلب المجموعات فقط (groups, supergroups, channels)
                if dialog.is_group or dialog.is_channel:
                    group_info = {
                        'id': dialog.id,
                        'name': dialog.name,
                        'title': dialog.title,
                        'username': dialog.entity.username,
                        'link': f"https://t.me/{dialog.entity.username}" if dialog.entity.username else None,
                        'chat_id': dialog.entity.id,
                        'is_group': dialog.is_group,
                        'is_channel': dialog.is_channel,
                        'participants_count': getattr(dialog.entity, 'participants_count', 0)
                    }
                    groups.append(group_info)
                    logger.debug(f"Found group: {dialog.name}")
            
            # تخزين في الكاش
            self.groups_cache[session_string] = groups
            logger.info(f"✅ Found {len(groups)} groups in account")
            
            return groups
            
        except Exception as e:
            logger.error(f"Error fetching groups: {e}")
            return []


    async def refresh_all_groups(self, update, context):
        """تحديث قائمة المجموعات لجميع حسابات المدير"""
        
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        active_accounts = [a for a in accounts if a['active'] == 1]
        
        if not active_accounts:
            await update.message.reply_text("❌ لا يوجد حسابات مفعلة")
            return
        
        await update.message.reply_text("⏳ جاري تحديث المجموعات...")
        
        results = {}
        total_groups = 0
        
        for acc in active_accounts:
            session_string = acc['session']
            # مسح الكاش للحصول على بيانات جديدة
            if session_string in self.groups_cache:
                del self.groups_cache[session_string]
            
            groups = await self.fetch_all_groups(session_string)
            total_groups += len(groups)
            results[acc['id']] = {
                'account_id': acc['id'],
                'groups_count': len(groups)
            }
        
        await update.message.reply_text(f"✅ تم التحديث! إجمالي المجموعات: {total_groups}")


    # ==================================================
    # START / STOP PUBLISHING
    # ==================================================

    def start_publishing(self, admin_id: int) -> bool:

        if admin_id in self.publish_tasks:
            return False

        task = asyncio.create_task(
            self._publish_loop(admin_id)
        )

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
    # MAIN PUBLISH LOOP (النشر في جميع المجموعات تلقائياً)
    # ==================================================

    async def _publish_loop(self, admin_id: int):

        logger.info(f"[PUBLISH LOOP STARTED] for admin {admin_id}")
        
        try:
            while True:

                # جلب الحسابات والإعلانات من قاعدة البيانات
                accounts = self.db.get_accounts(admin_id)
                ads = self.db.get_ads(admin_id)

                # تصفية الحسابات النشطة
                active_accounts = [a for a in accounts if a['active'] == 1]
                
                # تصفية الإعلانات النشطة
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
                    await asyncio.sleep(30)
                    continue
                    
                if not active_ads:
                    logger.warning("No active ads")
                    await asyncio.sleep(30)
                    continue

                # لكل حساب، جلب جميع المجموعات التي فيه
                for acc in active_accounts:
                    
                    session_string = acc['session']
                    
                    if not session_string:
                        logger.error(f"No session for account ID: {acc['id']}")
                        continue

                    # جلب جميع المجموعات من هذا الحساب
                    groups = await self.fetch_all_groups(session_string)
                    
                    if not groups:
                        logger.warning(f"No groups found for account {acc['id']}")
                        continue

                    logger.info(f"📊 Account {acc['id']} has {len(groups)} groups")

                    try:
                        client = await self.get_client(session_string)
                        logger.info(f"✅ Connected to account ID: {acc['id']}")
                    except Exception as e:
                        logger.error(f"[SESSION ERROR] {e}")
                        continue

                    # خلط الترتيب
                    random.shuffle(active_ads)
                    random.shuffle(groups)

                    # النشر في جميع المجموعات
                    for ad in active_ads:
                        
                        ad_type = ad['type']
                        ad_text = ad['text'] or ""
                        ad_media = ad['media_path'] or None

                        for group in groups:
                            
                            # تحديد طريقة الإرسال
                            if group['username']:
                                target = f"@{group['username']}"
                            else:
                                target = group['chat_id']

                            try:
                                logger.info(f"📤 Sending to {group['name']} ({target})")
                                
                                if ad_type == "text":
                                    await client.send_message(target, ad_text)

                                elif ad_type == "photo":
                                    if ad_media:
                                        await client.send_file(
                                            target,
                                            ad_media,
                                            caption=ad_text
                                        )
                                    else:
                                        await client.send_message(target, ad_text)

                                elif ad_type == "contact":
                                    if ad_media:
                                        await client.send_file(target, ad_media)
                                    else:
                                        await client.send_message(target, ad_text)
                                
                                else:
                                    await client.send_message(target, ad_text)

                                logger.info(f"[SENT] ✅ Account {acc['id']} -> {group['name']}")
                                
                                # انتظر بعد كل رسالة
                                await asyncio.sleep(self.publish_delay)

                            except FloodWaitError as e:
                                logger.warning(f"[FLOODWAIT] Need to wait {e.seconds} seconds")
                                await asyncio.sleep(e.seconds)

                            except Exception as e:
                                logger.error(f"[SEND ERROR] to {group['name']}: {e}")
                                await asyncio.sleep(3)

                # انتظر بين كل دورة كاملة
                logger.info("🔄 Cycle completed, refreshing groups and waiting 60 seconds...")
                
                # مسح الكاش للحصول على المجموعات الجديدة في الدورة التالية
                self.groups_cache.clear()
                
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info(f"[PUBLISH LOOP CANCELLED] admin {admin_id}")

        except Exception as e:
            logger.exception(f"[PUBLISH LOOP ERROR] {e}")


    # ==================================================
    # TEST PUBLISH (للتجربة)
    # ==================================================

    async def test_publish_once(self, update, context):
        """تجربة نشر رسالة تجريبية في أول 3 مجموعات"""
        
        admin_id = update.effective_user.id
        
        accounts = self.db.get_accounts(admin_id)
        active_accounts = [a for a in accounts if a['active'] == 1]
        
        if not active_accounts:
            await update.message.reply_text("❌ لا يوجد حسابات مفعلة")
            return
        
        await update.message.reply_text("⏳ جاري جلب المجموعات وتجربة النشر...")
        
        total_groups = 0
        sent_count = 0
        
        for acc in active_accounts:
            session_string = acc['session']
            
            # جلب المجموعات
            groups = await self.fetch_all_groups(session_string)
            total_groups += len(groups)
            
            if not groups:
                await update.message.reply_text(f"⚠️ لا توجد مجموعات في الحساب {acc['id']}")
                continue
            
            try:
                client = await self.get_client(session_string)
                
                # جرب أول 3 مجموعات فقط للتجربة
                for group in groups[:3]:
                    target = f"@{group['username']}" if group['username'] else group['chat_id']
                    
                    try:
                        await client.send_message(
                            target, 
                            "🧪 **رسالة تجربة من البوت** ✅\n\nالبوت يعمل بشكل جيد وسينشر في جميع المجموعات تلقائياً!"
                        )
                        sent_count += 1
                        await update.message.reply_text(f"✅ تم الإرسال إلى: {group['name']}")
                        
                    except Exception as e:
                        await update.message.reply_text(f"❌ فشل الإرسال إلى {group['name']}: {str(e)[:50]}")
                        
            except Exception as e:
                await update.message.reply_text(f"❌ خطأ في الحساب: {str(e)[:50]}")
        
        await update.message.reply_text(
            f"📊 **النتيجة النهائية:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📦 إجمالي المجموعات: {total_groups}\n"
            f"✅ تم الإرسال إلى: {sent_count} مجموعة\n"
            f"🚀 البوت جاهز للنشر الكامل!"
        )


    async def show_all_groups(self, update, context):
        """عرض جميع المجموعات من جميع الحسابات"""
        
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        active_accounts = [a for a in accounts if a['active'] == 1]
        
        if not active_accounts:
            await update.message.reply_text("❌ لا يوجد حسابات مفعلة")
            return
        
        await update.message.reply_text("⏳ جاري جلب المجموعات...")
        
        result = "📋 **جميع المجموعات في حساباتك:**\n\n"
        
        for acc in active_accounts:
            session_string = acc['session']
            groups = await self.fetch_all_groups(session_string)
            
            result += f"👤 **الحساب {acc['id']}**:\n"
            result += f"📦 عدد المجموعات: {len(groups)}\n\n"
            
            # عرض أول 20 مجموعة
            for i, group in enumerate(groups[:20], 1):
                result += f"  {i}. {group['name'][:40]}\n"
            
            if len(groups) > 20:
                result += f"  ... و {len(groups) - 20} مجموعة أخرى\n"
            
            result += "\n" + "━" * 30 + "\n\n"
            
            if len(result) > 4000:
                result = result[:4000] + "\n\n... تم اقتصار العرض"
                break
        
        await update.message.reply_text(result, parse_mode='Markdown')


    async def get_status(self, update, context):
        """عرض حالة البوت"""
        
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        ads = self.db.get_ads(admin_id)
        
        active_accounts = [a for a in accounts if a['active'] == 1]
        
        is_publishing = admin_id in self.publish_tasks
        
        status_text = f"""
📊 **حالة البوت**
━━━━━━━━━━━━━━━━━━━
🚀 حالة النشر: {'✅ شغال' if is_publishing else '⭕ متوقف'}
👥 عدد الحسابات: {len(accounts)}
✅ الحسابات المفعلة: {len(active_accounts)}
📢 عدد الإعلانات: {len(ads)}
⏱ وقت التأخير: {self.publish_delay} ثانية
━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(status_text, parse_mode='Markdown')


    # ==================================================
    # SETTINGS
    # ==================================================

    def set_publish_delay(self, delay_seconds: float):
        """تغيير وقت التأخير بين الرسائل"""
        self.publish_delay = delay_seconds
        logger.info(f"[SETTINGS] Publish delay set to {delay_seconds} seconds")


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
