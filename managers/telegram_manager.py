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

API_ID = 123456        # ضع api_id الحقيقي
API_HASH = "API_HASH"  # ضع api_hash الحقيقي


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
        self.publish_delay = 60.0  # تغيير إلى 60 ثانية بين كل رسالة


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
    # MAIN PUBLISH LOOP (REAL)
    # ==================================================

    async def _publish_loop(self, admin_id: int):

        logger.info(f"[PUBLISH LOOP STARTED] for admin {admin_id}")
        
        try:
            while True:

                # جلب البيانات من قاعدة البيانات
                accounts = self.db.get_accounts()
                ads = self.db.get_ads()
                groups = self.db.get_groups()

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
                active_accounts = [a for a in accounts if a.get('active', 0) == 1]
                active_groups = [g for g in groups if g.get('active', 0) == 1]
                active_ads = [a for a in ads if a.get('active', 0) == 1]

                logger.info(f"Active accounts: {len(active_accounts)}, Active groups: {len(active_groups)}, Active ads: {len(active_ads)}")

                if not active_accounts or not active_groups or not active_ads:
                    logger.warning("Missing active accounts, groups or ads")
                    await asyncio.sleep(30)
                    continue

                # اخلط الترتيب
                random.shuffle(active_accounts)
                random.shuffle(active_ads)
                random.shuffle(active_groups)

                # حلقة واحدة: حساب ← إعلان ← مجموعة واحدة فقط ثم انتقل
                for acc in active_accounts:
                    
                    session_string = acc.get('session_string') or acc.get('session')
                    
                    if not session_string:
                        logger.error(f"No session for account: {acc}")
                        continue

                    try:
                        client = await self.get_client(session_string)
                        logger.info(f"Connected to account: {acc.get('username', 'Unknown')}")
                    except Exception as e:
                        logger.error(f"[SESSION ERROR] {e}")
                        continue

                    for ad in active_ads:
                        
                        ad_type = ad.get('type', 'text')
                        ad_text = ad.get('content', '') or ad.get('text', '')
                        ad_media = ad.get('media', None)

                        for group in active_groups:
                            
                            group_link = group.get('link') or group.get('username') or group.get('group_id')
                            
                            if not group_link:
                                logger.error(f"No link for group: {group}")
                                continue

                            try:
                                logger.info(f"Sending to {group_link} from {acc.get('username', 'Unknown')}")
                                
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

                                logger.info(f"[SENT] ✅ {acc.get('username')} -> {group_link}")
                                
                                # انتظر بعد كل رسالة
                                await asyncio.sleep(self.publish_delay)

                            except FloodWaitError as e:
                                logger.warning(f"[FLOODWAIT] Need to wait {e.seconds} seconds")
                                await asyncio.sleep(e.seconds)

                            except Exception as e:
                                logger.error(f"[SEND ERROR] {e}")
                                await asyncio.sleep(5)

                # انتظر بين كل دورة كاملة
                logger.info("Cycle completed, waiting 60 seconds...")
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info(f"[PUBLISH LOOP CANCELLED] admin {admin_id}")

        except Exception as e:
            logger.exception(f"[PUBLISH LOOP ERROR] {e}")

    # ==================================================
    # TEST PUBLISH (للتجربة)
    # ==================================================

    async def test_publish_once(self, admin_id: int) -> str:
        """تجربة نشر مرة واحدة"""
        
        accounts = self.db.get_accounts()
        ads = self.db.get_ads()
        groups = self.db.get_groups()
        
        active_accounts = [a for a in accounts if a.get('active', 0) == 1]
        active_groups = [g for g in groups if g.get('active', 0) == 1]
        active_ads = [a for a in ads if a.get('active', 0) == 1]
        
        if not active_accounts:
            return "❌ لا يوجد حسابات مفعلة"
        if not active_groups:
            return "❌ لا يوجد مجموعات مفعلة"
        if not active_ads:
            return "❌ لا يوجد إعلانات مفعلة"
        
        sent_count = 0
        
        for acc in active_accounts[:1]:  # جرب أول حساب فقط
            session_string = acc.get('session_string') or acc.get('session')
            
            try:
                client = await self.get_client(session_string)
                
                for ad in active_ads[:1]:  # جرب أول إعلان فقط
                    ad_text = ad.get('content', '') or ad.get('text', '')
                    
                    for group in active_groups[:1]:  # جرب أول مجموعة فقط
                        group_link = group.get('link') or group.get('username')
                        
                        try:
                            await client.send_message(group_link, "🧪 رسالة تجربة من البوت")
                            sent_count += 1
                            logger.info(f"Test message sent to {group_link}")
                        except Exception as e:
                            logger.error(f"Test send error: {e}")
                            return f"❌ فشل الإرسال: {str(e)[:50]}"
                            
            except Exception as e:
                return f"❌ خطأ في الحساب: {str(e)[:50]}"
        
        return f"✅ تم إرسال {sent_count} رسالة تجريبية"


    # ==================================================
    # CLEANUP (OPTIONAL)
    # ==================================================

    async def shutdown(self):

        for task in self.publish_tasks.values():
            task.cancel()

        for client in self.clients.values():
            await client.disconnect()

        self.publish_tasks.clear()
        self.clients.clear()
