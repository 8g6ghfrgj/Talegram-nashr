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
        self.publish_delay = 60.0  # 60 ثانية بين كل رسالة


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
    # START / STOP PUBLISHING
    # ==================================================

    def start_publishing(self, admin_id: int) -> bool:

        if admin_id in self.publish_tasks:
            return False  # already running

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
    # MAIN PUBLISH LOOP
    # ==================================================

    async def _publish_loop(self, admin_id: int):

        logger.info(f"[PUBLISH LOOP STARTED] for admin {admin_id}")
        
        try:
            while True:

                # جلب البيانات من قاعدة البيانات
                accounts = self.db.get_accounts(admin_id)
                ads = self.db.get_ads(admin_id)
                groups = self.db.get_groups(admin_id)

                logger.info(f"📊 Raw data - Accounts: {len(accounts)}, Ads: {len(ads)}, Groups: {len(groups)}")

                # تحقق من صحة البيانات
                if not accounts:
                    logger.warning("No accounts found")
                    await asyncio.sleep(30)
                    continue
                    
                if not ads:
                    logger.warning("No ads found")
                    await asyncio.sleep(30)
                    continue
                    
                if not groups:
                    logger.warning("No groups found")
                    await asyncio.sleep(30)
                    continue

                # تصفية الحسابات والمجموعات والإعلانات النشطة
                active_accounts = [a for a in accounts if a['active'] == 1]
                active_groups = [g for g in groups if g['status'] == 'active']
                active_ads = [a for a in ads if a['active'] == 1] if 'active' in ads[0].keys() else ads

                logger.info(f"✅ Active accounts: {len(active_accounts)}, Active groups: {len(active_groups)}, Active ads: {len(active_ads)}")

                if not active_accounts:
                    logger.warning("No active accounts")
                    await asyncio.sleep(30)
                    continue
                    
                if not active_groups:
                    logger.warning("No active groups")
                    await asyncio.sleep(30)
                    continue
                    
                if not active_ads:
                    logger.warning("No active ads")
                    await asyncio.sleep(30)
                    continue

                # اخلط الترتيب
                random.shuffle(active_accounts)
                random.shuffle(active_ads)
                random.shuffle(active_groups)

                # حلقة النشر
                for acc in active_accounts:
                    
                    # الوصول إلى session من العمود 'session'
                    session_string = acc['session']
                    
                    if not session_string:
                        logger.error(f"No session for account ID: {acc['id']}")
                        continue

                    try:
                        client = await self.get_client(session_string)
                        logger.info(f"✅ Connected to account ID: {acc['id']}")
                    except Exception as e:
                        logger.error(f"[SESSION ERROR] {e}")
                        continue

                    for ad in active_ads:
                        
                        ad_type = ad['type']  # 'text', 'photo', 'contact'
                        ad_text = ad['text'] or ""
                        ad_media = ad['media_path'] or None

                        for group in active_groups:
                            
                            group_link = group['link']
                            
                            if not group_link:
                                logger.error(f"No link for group ID: {group['id']}")
                                continue

                            try:
                                logger.info(f"📤 Sending to {group_link} from account {acc['id']}")
                                
                                if ad_type == "text":
                                    await client.send_message(group_link, ad_text)

                                elif ad_type == "photo":
                                    if ad_media:
                                        await client.send_file(
                                            group_link,
                                            ad_media,
                                            caption=ad_text
                                        )
                                    else:
                                        await client.send_message(group_link, ad_text)

                                elif ad_type == "contact":
                                    if ad_media:
                                        await client.send_file(group_link, ad_media)
                                    else:
                                        await client.send_message(group_link, ad_text)
                                
                                else:
                                    await client.send_message(group_link, ad_text)

                                logger.info(f"[SENT] ✅ Account {acc['id']} -> {group_link}")
                                
                                # انتظر بعد كل رسالة
                                await asyncio.sleep(self.publish_delay)

                            except FloodWaitError as e:
                                logger.warning(f"[FLOODWAIT] Need to wait {e.seconds} seconds")
                                await asyncio.sleep(e.seconds)

                            except Exception as e:
                                logger.error(f"[SEND ERROR] {e}")
                                await asyncio.sleep(5)

                # انتظر بين كل دورة كاملة
                logger.info("🔄 Cycle completed, waiting 60 seconds...")
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info(f"[PUBLISH LOOP CANCELLED] admin {admin_id}")

        except Exception as e:
            logger.exception(f"[PUBLISH LOOP ERROR] {e}")


    # ==================================================
    # TEST PUBLISH (للتجربة)
    # ==================================================

    async def test_publish_once(self, update, context):
        """تجربة نشر رسالة تجريبية مرة واحدة"""
        
        admin_id = update.effective_user.id
        
        # جلب البيانات
        accounts = self.db.get_accounts(admin_id)
        groups = self.db.get_groups(admin_id)
        
        # تصفية العناصر النشطة
        active_accounts = [a for a in accounts if a['active'] == 1]
        active_groups = [g for g in groups if g['status'] == 'active']
        
        if not active_accounts:
            await update.message.reply_text("❌ لا يوجد حسابات مفعلة")
            return
            
        if not active_groups:
            await update.message.reply_text("❌ لا يوجد مجموعات مفعلة")
            return
        
        await update.message.reply_text("⏳ جاري تجربة النشر...")
        
        sent_count = 0
        errors = []
        
        # جرب أول حساب وأول مجموعة فقط
        for acc in active_accounts[:1]:
            session_string = acc['session']
            
            try:
                client = await self.get_client(session_string)
                me = await client.get_me()
                
                for group in active_groups[:1]:
                    group_link = group['link']
                    
                    try:
                        await client.send_message(
                            group_link, 
                            "🧪 رسالة تجربة من البوت ✅\n\nالبوت يعمل بشكل جيد!"
                        )
                        sent_count += 1
                        await update.message.reply_text(f"✅ تم الإرسال إلى {group_link}")
                        
                    except Exception as e:
                        error_msg = f"❌ فشل الإرسال إلى {group_link}: {str(e)[:50]}"
                        errors.append(error_msg)
                        await update.message.reply_text(error_msg)
                        
            except Exception as e:
                await update.message.reply_text(f"❌ خطأ في الحساب: {str(e)[:50]}")
        
        if sent_count > 0:
            await update.message.reply_text(f"✅ تم إرسال {sent_count} رسالة تجريبية بنجاح")
        else:
            await update.message.reply_text(f"❌ فشل الإرسال: {', '.join(errors)}")


    async def test_account_connection(self, update, context, account_id: int):
        """اختبار اتصال حساب معين"""
        
        admin_id = update.effective_user.id
        accounts = self.db.get_accounts(admin_id)
        
        account = None
        for acc in accounts:
            if acc['id'] == account_id:
                account = acc
                break
        
        if not account:
            await update.message.reply_text("❌ الحساب غير موجود")
            return
        
        await update.message.reply_text("⏳ جاري اختبار الاتصال...")
        
        try:
            client = await self.get_client(account['session'])
            me = await client.get_me()
            await update.message.reply_text(
                f"✅ الحساب يعمل بشكل جيد\n\n"
                f"👤 الاسم: {me.first_name}\n"
                f"📝 المعرف: @{me.username}\n"
                f"🆔 الايدي: {me.id}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الاتصال: {str(e)[:100]}")


    # ==================================================
    # SETTINGS
    # ==================================================

    def set_publish_delay(self, delay_seconds: float):
        """تغيير وقت التأخير بين الرسائل"""
        self.publish_delay = delay_seconds
        logger.info(f"[SETTINGS] Publish delay set to {delay_seconds} seconds")


    # ==================================================
    # STATUS
    # ==================================================

    def is_publishing(self, admin_id: int) -> bool:
        """التحقق من حالة النشر"""
        return admin_id in self.publish_tasks


    def get_status(self, admin_id: int) -> dict:
        """الحصول على حالة النشر كاملة"""
        accounts = self.db.get_accounts(admin_id)
        ads = self.db.get_ads(admin_id)
        groups = self.db.get_groups(admin_id)
        
        active_accounts = len([a for a in accounts if a['active'] == 1])
        active_groups = len([g for g in groups if g['status'] == 'active'])
        
        return {
            "is_publishing": admin_id in self.publish_tasks,
            "accounts_count": len(accounts),
            "active_accounts": active_accounts,
            "ads_count": len(ads),
            "groups_count": len(groups),
            "active_groups": active_groups,
            "publish_delay": self.publish_delay
        }


    # ==================================================
    # CLEANUP
    # ==================================================

    async def shutdown(self):
        """إيقاف جميع المهام وإغلاق الاتصالات"""

        for admin_id, task in self.publish_tasks.items():
            task.cancel()
            logger.info(f"[SHUTDOWN] Cancelled publish task for admin {admin_id}")

        for session_string, client in self.clients.items():
            await client.disconnect()
            logger.info(f"[SHUTDOWN] Disconnected client")

        self.publish_tasks.clear()
        self.clients.clear()
        logger.info("[SHUTDOWN] Complete")
