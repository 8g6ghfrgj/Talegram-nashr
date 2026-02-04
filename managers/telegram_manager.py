import asyncio
import threading
import os
import random
import logging
from datetime import datetime

from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import InputPeerEmpty

from config import DELAY_SETTINGS, OWNER_ID

logger = logging.getLogger(__name__)

class TelegramBotManager:
    def __init__(self, db):
        self.db = db
        
        # إعدادات التأخير
        self.delay_settings = DELAY_SETTINGS
        
        # حالات المهام
        self.publishing_active = {}
        self.publishing_tasks = {}
        self.private_reply_active = {}
        self.private_reply_tasks = {}
        self.group_reply_active = {}
        self.group_reply_tasks = {}
        self.random_reply_active = {}
        self.random_reply_tasks = {}
        self.join_groups_active = {}
        self.join_groups_tasks = {}
        
        # ذاكرة التخزين المؤقت للعملاء
        self.client_cache = {}
        
        # قفل للتزامن
        self.lock = threading.Lock()
        
        # إحصائيات
        self.stats = {
            'publish_count': 0,
            'reply_count': 0,
            'join_count': 0,
            'errors': 0
        }
        
        logger.info("✅ تم تهيئة مدير تليجرام")
    
    async def get_client(self, session_string):
        """الحصول على عميل من الذاكرة المؤقتة"""
        if session_string not in self.client_cache:
            try:
                # إنشاء عميل جديد
                client = TelegramClient(
                    StringSession(session_string),
                    api_id=1,  # يمكنك استبدال هذا بـ API ID الحقيقي
                    api_hash="b"  # يمكنك استبدال هذا بـ API Hash الحقيقي
                )
                
                await client.connect()
                
                # التحقق من تفعيل الجلسة
                if await client.is_user_authorized():
                    self.client_cache[session_string] = client
                    logger.debug(f"✅ تم توصيل العميل للجلسة: {session_string[:20]}...")
                else:
                    await client.disconnect()
                    logger.error(f"❌ جلسة غير مفعلة: {session_string[:20]}...")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ خطأ في الاتصال بالجلسة: {str(e)}")
                return None
        
        return self.client_cache.get(session_string)
    
    async def cleanup_client(self, session_string):
        """تنظيف العميل من الذاكرة المؤقتة"""
        if session_string in self.client_cache:
            try:
                client = self.client_cache[session_string]
                await client.disconnect()
                logger.debug(f"✅ تم فصل العميل للجلسة: {session_string[:20]}...")
            except Exception as e:
                logger.error(f"❌ خطأ في فصل العميل: {str(e)}")
            finally:
                del self.client_cache[session_string]
    
    async def cleanup_all(self):
        """تنظيف جميع العملاء"""
        logger.info("🧹 جاري تنظيف جميع العملاء...")
        for session_string in list(self.client_cache.keys()):
            await self.cleanup_client(session_string)
        logger.info("✅ تم تنظيف جميع العملاء")
    
    # ============ مهام النشر ============
    
    async def publish_to_groups_task(self, admin_id):
        """مهمة النشر في المجموعات مع تأخير 60 ثانية بين نشر القروبات"""
        logger.info(f"🚀 بدأ النشر للمشرف {admin_id}")
        
        while self.publishing_active.get(admin_id, False):
            try:
                # الحصول على الحسابات النشطة
                accounts = self.db.get_active_publishing_accounts(admin_id)
                
                # الحصول على الإعلانات
                ads = self.db.get_ads(admin_id)
                
                if not accounts or not ads:
                    logger.info(f"⏳ انتظار للحسابات/إعلانات للمشرف {admin_id}")
                    await asyncio.sleep(self.delay_settings['publishing']['between_cycles'])
                    continue
                
                logger.info(f"📊 النشر للمشرف {admin_id}: {len(accounts)} حساب، {len(ads)} إعلان")
                
                # النشر من كل حساب
                for account in accounts:
                    if not self.publishing_active.get(admin_id, False):
                        break
                    
                    account_id, session_string, name, username = account
                    
                    try:
                        # الحصول على العميل
                        client = await self.get_client(session_string)
                        if not client:
                            logger.error(f"❌ فشل الحصول على العميل للحساب {name}")
                            continue
                        
                        # الحصول على المجموعات
                        try:
                            dialogs = await client.get_dialogs(limit=100)
                        except Exception as e:
                            logger.error(f"❌ خطأ في جلب الدردشات للحساب {name}: {str(e)}")
                            await self.cleanup_client(session_string)
                            continue
                        
                        # نشر في كل مجموعة
                        for dialog in dialogs:
                            if not self.publishing_active.get(admin_id, False):
                                break
                            
                            # التحقق من أن الدردشة مجموعة أو قناة
                            if dialog.is_group or dialog.is_channel:
                                try:
                                    logger.info(f"📨 نشر في {dialog.name} بواسطة {name}")
                                    
                                    # نشر جميع الإعلانات
                                    for ad in ads:
                                        if not self.publishing_active.get(admin_id, False):
                                            break
                                        
                                        ad_id, ad_type, ad_text, media_path, file_type, added_date, ad_admin_id, is_encoded = ad
                                        
                                        try:
                                            # التحقق من وجود الملف إذا كان مطلوباً
                                            if ad_type in ['photo', 'contact'] and media_path:
                                                if not os.path.exists(media_path):
                                                    logger.error(f"❌ الملف غير موجود: {media_path}")
                                                    continue
                                            
                                            # النشر حسب نوع الإعلان
                                            if ad_type == 'text':
                                                await client.send_message(dialog.id, ad_text)
                                                logger.info(f"✅ نشر نص في {dialog.name} بواسطة {name}")
                                                
                                            elif ad_type == 'photo' and media_path:
                                                await client.send_file(dialog.id, media_path, caption=ad_text)
                                                logger.info(f"✅ نشر صورة في {dialog.name} بواسطة {name}")
                                                
                                            elif ad_type == 'contact' and media_path:
                                                if media_path.endswith('.vcf'):
                                                    with open(media_path, 'rb') as f:
                                                        await client.send_file(
                                                            dialog.id, 
                                                            f, 
                                                            caption=ad_text,
                                                            file_name="تسوي سكليف صحتي واتساب.vcf"
                                                        )
                                                    logger.info(f"✅ نشر جهة اتصال في {dialog.name} بواسطة {name}")
                                            
                                            # تحديث الإحصائيات
                                            self.stats['publish_count'] += 1
                                            self.db.update_account_activity(account_id)
                                            
                                            # تأخير بين الإعلانات في نفس المجموعة
                                            await asyncio.sleep(self.delay_settings['publishing']['between_ads'])
                                            
                                        except errors.FloodWaitError as e:
                                            logger.warning(f"⏳ Flood wait للحساب {name}: {e.seconds} ثانية")
                                            await asyncio.sleep(e.seconds + 1)
                                            continue
                                            
                                        except Exception as e:
                                            logger.error(f"❌ فشل نشر الإعلان {ad_id}: {str(e)}")
                                            self.stats['errors'] += 1
                                            continue
                                    
                                    # 🔴 **تأخير 60 ثانية بين نشر القروبات** 🔴
                                    logger.info(f"⏱️ تأخير 60 ثانية قبل المجموعة التالية")
                                    await asyncio.sleep(self.delay_settings['publishing']['group_publishing_delay'])
                                    
                                except Exception as e:
                                    logger.error(f"❌ فشل النشر في {dialog.name}: {str(e)}")
                                    continue
                        
                        # تأخير بين المجموعات المختلفة
                        await asyncio.sleep(self.delay_settings['publishing']['between_groups'])
                        
                    except Exception as e:
                        logger.error(f"❌ خطأ في الحساب {name}: {str(e)}")
                        await self.cleanup_client(session_string)
                        continue
                
                # تأخير بين الدورات
                logger.info(f"⏳ انتظار {self.delay_settings['publishing']['between_cycles']} ثانية للدورة القادمة")
                await asyncio.sleep(self.delay_settings['publishing']['between_cycles'])
                
            except Exception as e:
                logger.error(f"❌ خطأ في عملية النشر: {str(e)}")
                await asyncio.sleep(10)
        
        logger.info(f"⏹️ توقف النشر للمشرف {admin_id}")
    
    # ============ مهام الردود ============
    
    async def handle_private_messages_task(self, admin_id):
        """مهمة الرد على الرسائل الخاصة"""
        logger.info(f"💬 بدأ الرد في الخاص للمشرف {admin_id}")
        
        while self.private_reply_active.get(admin_id, False):
            try:
                accounts = self.db.get_active_publishing_accounts(admin_id)
                private_replies = self.db.get_private_replies(admin_id)
                
                if not accounts or not private_replies:
                    await asyncio.sleep(self.delay_settings['private_reply']['between_cycles'])
                    continue
                
                for account in accounts:
                    if not self.private_reply_active.get(admin_id, False):
                        break
                    
                    account_id, session_string, name, username = account
                    
                    try:
                        client = await self.get_client(session_string)
                        if not client:
                            continue
                        
                        # الحصول على الرسائل الجديدة
                        async for message in client.iter_messages(None, limit=20):
                            if not self.private_reply_active.get(admin_id, False):
                                break
                            
                            if message.is_private and not message.out:
                                for reply in private_replies:
                                    reply_id, reply_text, is_active, added_date, reply_admin_id, is_encoded = reply
                                    
                                    if is_active:
                                        try:
                                            await client.send_message(message.sender_id, reply_text)
                                            logger.info(f"💬 رد على رسالة خاصة بواسطة {name}")
                                            
                                            self.stats['reply_count'] += 1
                                            self.db.update_account_activity(account_id)
                                            
                                            # تأخير بين الردود
                                            await asyncio.sleep(self.delay_settings['private_reply']['between_replies'])
                                            break
                                            
                                        except errors.FloodWaitError as e:
                                            logger.warning(f"⏳ Flood wait في الرد الخاص: {e.seconds} ثانية")
                                            await asyncio.sleep(e.seconds + 1)
                                            continue
                                        except Exception as e:
                                            logger.error(f"❌ فشل الرد في الخاص: {str(e)}")
                                            continue
                        
                    except Exception as e:
                        logger.error(f"❌ خطأ في الحساب {name}: {str(e)}")
                        await self.cleanup_client(session_string)
                        continue
                
                await asyncio.sleep(self.delay_settings['private_reply']['between_cycles'])
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الرسائل الخاصة: {str(e)}")
                await asyncio.sleep(5)
        
        logger.info(f"⏹️ توقف الرد في الخاص للمشرف {admin_id}")
    
    async def handle_group_replies_task(self, admin_id):
        """مهمة الردود في المجموعات"""
        logger.info(f"👥 بدأ الرد في القروبات للمشرف {admin_id}")
        
        while self.group_reply_active.get(admin_id, False):
            try:
                accounts = self.db.get_active_publishing_accounts(admin_id)
                text_replies = self.db.get_group_text_replies(admin_id)
                photo_replies = self.db.get_group_photo_replies(admin_id)
                
                if not accounts or (not text_replies and not photo_replies):
                    await asyncio.sleep(self.delay_settings['group_reply']['between_cycles'])
                    continue
                
                for account in accounts:
                    if not self.group_reply_active.get(admin_id, False):
                        break
                    
                    account_id, session_string, name, username = account
                    
                    try:
                        client = await self.get_client(session_string)
                        if not client:
                            continue
                        
                        dialogs = await client.get_dialogs(limit=50)
                        
                        for dialog in dialogs:
                            if not self.group_reply_active.get(admin_id, False):
                                break
                            
                            if dialog.is_group:
                                try:
                                    async for message in client.iter_messages(dialog.id, limit=5):
                                        if not self.group_reply_active.get(admin_id, False):
                                            break
                                        
                                        if message.text and not message.out:
                                            # الردود النصية
                                            for reply in text_replies:
                                                reply_id, trigger, reply_text, is_active, added_date, reply_admin_id, is_encoded = reply
                                                
                                                if is_active and trigger.lower() in message.text.lower():
                                                    try:
                                                        await client.send_message(dialog.id, reply_text, reply_to=message.id)
                                                        logger.info(f"💬 رد على {trigger} في {dialog.name} بواسطة {name}")
                                                        
                                                        self.stats['reply_count'] += 1
                                                        self.db.update_account_activity(account_id)
                                                        
                                                        await asyncio.sleep(self.delay_settings['group_reply']['between_replies'])
                                                        break
                                                        
                                                    except errors.FloodWaitError as e:
                                                        logger.warning(f"⏳ Flood wait في الرد الجماعي: {e.seconds} ثانية")
                                                        await asyncio.sleep(e.seconds + 1)
                                                        continue
                                                    except Exception as e:
                                                        logger.error(f"❌ فشل الرد الجماعي: {str(e)}")
                                                        continue
                                            
                                            # الردود مع الصور
                                            for reply in photo_replies:
                                                reply_id, trigger, reply_text, media_path, is_active, added_date, reply_admin_id, is_encoded = reply
                                                
                                                if is_active and trigger.lower() in message.text.lower() and os.path.exists(media_path):
                                                    try:
                                                        await client.send_file(dialog.id, media_path, caption=reply_text, reply_to=message.id)
                                                        logger.info(f"🖼️ رد بصورة على {trigger} في {dialog.name} بواسطة {name}")
                                                        
                                                        self.stats['reply_count'] += 1
                                                        self.db.update_account_activity(account_id)
                                                        
                                                        await asyncio.sleep(self.delay_settings['group_reply']['between_replies'])
                                                        break
                                                        
                                                    except errors.FloodWaitError as e:
                                                        logger.warning(f"⏳ Flood wait في الرد بالصورة: {e.seconds} ثانية")
                                                        await asyncio.sleep(e.seconds + 1)
                                                        continue
                                                    except Exception as e:
                                                        logger.error(f"❌ فشل الرد بالصورة: {str(e)}")
                                                        continue
                                        
                                except Exception as e:
                                    logger.error(f"❌ فشل في المجموعة {dialog.name}: {str(e)}")
                                    continue
                        
                    except Exception as e:
                        logger.error(f"❌ خطأ في الحساب {name}: {str(e)}")
                        await self.cleanup_client(session_string)
                        continue
                
                await asyncio.sleep(self.delay_settings['group_reply']['between_cycles'])
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الردود الجماعية: {str(e)}")
                await asyncio.sleep(5)
        
        logger.info(f"⏹️ توقف الرد في القروبات للمشرف {admin_id}")
    
    async def handle_random_replies_task(self, admin_id):
        """مهمة الردود العشوائية في القروبات"""
        logger.info(f"🎲 بدأ الرد العشوائي للمشرف {admin_id}")
        
        while self.random_reply_active.get(admin_id, False):
            try:
                accounts = self.db.get_active_publishing_accounts(admin_id)
                random_replies = self.db.get_group_random_replies(admin_id)
                
                if not accounts or not random_replies:
                    await asyncio.sleep(self.delay_settings['random_reply']['between_cycles'])
                    continue
                
                for account in accounts:
                    if not self.random_reply_active.get(admin_id, False):
                        break
                    
                    account_id, session_string, name, username = account
                    
                    try:
                        client = await self.get_client(session_string)
                        if not client:
                            continue
                        
                        dialogs = await client.get_dialogs(limit=30)
                        
                        for dialog in dialogs:
                            if not self.random_reply_active.get(admin_id, False):
                                break
                            
                            if dialog.is_group:
                                try:
                                    async for message in client.iter_messages(dialog.id, limit=3):
                                        if not self.random_reply_active.get(admin_id, False):
                                            break
                                        
                                        if message.text and not message.out and random.random() < 1.0:  # 100% رد
                                            random_reply = random.choice(random_replies)
                                            reply_id, reply_text, media_path, is_active, added_date, reply_admin_id, is_encoded, has_media = random_reply
                                            
                                            if is_active:
                                                try:
                                                    if has_media and media_path and os.path.exists(media_path):
                                                        await client.send_file(dialog.id, media_path, caption=reply_text, reply_to=message.id)
                                                        logger.info(f"🎲 رد عشوائي مع صورة في {dialog.name} بواسطة {name}")
                                                    else:
                                                        await client.send_message(dialog.id, reply_text, reply_to=message.id)
                                                        logger.info(f"🎲 رد عشوائي في {dialog.name} بواسطة {name}")
                                                    
                                                    self.stats['reply_count'] += 1
                                                    self.db.update_account_activity(account_id)
                                                    
                                                    await asyncio.sleep(self.delay_settings['random_reply']['between_replies'])
                                                    break
                                                    
                                                except errors.FloodWaitError as e:
                                                    logger.warning(f"⏳ Flood wait في الرد العشوائي: {e.seconds} ثانية")
                                                    await asyncio.sleep(e.seconds + 1)
                                                    continue
                                                except Exception as e:
                                                    logger.error(f"❌ فشل الرد العشوائي: {str(e)}")
                                                    continue
                                        
                                except Exception as e:
                                    logger.error(f"❌ فشل في المجموعة {dialog.name}: {str(e)}")
                                    continue
                        
                    except Exception as e:
                        logger.error(f"❌ خطأ في الحساب {name}: {str(e)}")
                        await self.cleanup_client(session_string)
                        continue
                
                await asyncio.sleep(self.delay_settings['random_reply']['between_cycles'])
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الردود العشوائية: {str(e)}")
                await asyncio.sleep(5)
        
        logger.info(f"⏹️ توقف الرد العشوائي للمشرف {admin_id}")
    
    # ============ مهام الانضمام للمجموعات ============
    
    async def join_groups_task(self, admin_id):
        """مهمة الانضمام إلى المجموعات"""
        logger.info(f"👥 بدأ الانضمام للمجموعات للمشرف {admin_id}")
        
        while self.join_groups_active.get(admin_id, False):
            try:
                accounts = self.db.get_active_publishing_accounts(admin_id)
                groups = self.db.get_groups(admin_id, status='pending')
                
                if not accounts or not groups:
                    logger.info(f"⏳ انتظار للمجموعات/حسابات للمشرف {admin_id}")
                    await asyncio.sleep(self.delay_settings['join_groups']['between_cycles'])
                    continue
                
                logger.info(f"📊 الانضمام للمشرف {admin_id}: {len(accounts)} حساب، {len(groups)} مجموعة معلقة")
                
                for account in accounts:
                    if not self.join_groups_active.get(admin_id, False):
                        break
                    
                    account_id, session_string, name, username = account
                    
                    for group in groups:
                        if not self.join_groups_active.get(admin_id, False):
                            break
                        
                        group_id, link, status, join_date, added_date, group_admin_id, last_checked = group
                        
                        try:
                            client = await self.get_client(session_string)
                            if not client:
                                continue
                            
                            success = await self.join_single_group(client, link)
                            
                            if success:
                                self.db.update_group_status(group_id, 'joined')
                                logger.info(f"✅ انضم الحساب {name} إلى المجموعة {link}")
                                
                                self.stats['join_count'] += 1
                                self.db.update_account_activity(account_id)
                            else:
                                self.db.update_group_status(group_id, 'failed')
                                logger.warning(f"❌ فشل انضمام {name} إلى {link}")
                            
                            # تأخير 90 ثانية بين الروابط
                            logger.info(f"⏱️ تأخير {self.delay_settings['join_groups']['between_links']} ثانية للرابط التالي")
                            await asyncio.sleep(self.delay_settings['join_groups']['between_links'])
                            
                        except Exception as e:
                            logger.error(f"❌ خطأ في الحساب {name}: {str(e)}")
                            await self.cleanup_client(session_string)
                            continue
                
                await asyncio.sleep(self.delay_settings['join_groups']['between_cycles'])
                
            except Exception as e:
                logger.error(f"❌ خطأ في عملية الانضمام: {str(e)}")
                await asyncio.sleep(5)
        
        logger.info(f"⏹️ توقف الانضمام للمجموعات للمشرف {admin_id}")
    
    async def join_single_group(self, client, group_link):
        """الانضمام إلى مجموعة واحدة"""
        try:
            logger.debug(f"🔗 محاولة الانضمام إلى: {group_link}")
            
            # تنظيف الرابط
            if group_link.startswith('https://'):
                group_link = group_link.replace('https://', '')
            
            if group_link.startswith('t.me/'):
                group_link = group_link.replace('t.me/', '')
            
            # التعامل مع أنواع الروابط المختلفة
            if group_link.startswith('+') or 'joinchat' in group_link:
                # رابط دعوة
                if group_link.startswith('+'):
                    invite_hash = group_link[1:]
                else:
                    invite_hash = group_link.split('/')[-1]
                
                await client(ImportChatInviteRequest(invite_hash))
                return True
            
            elif 'addlist' in group_link:
                # رابط قائمة (مجلد)
                folder_hash = group_link.split('/')[-1]
                try:
                    await client(ImportChatInviteRequest(folder_hash))
                    return True
                except errors.InviteHashExpiredError:
                    logger.info(f"⏰ رابط مجلد منتهي: {group_link}")
                    return False
                except:
                    try:
                        await client(JoinChannelRequest(f'@{folder_hash}'))
                        return True
                    except Exception as e:
                        logger.error(f"❌ فشل في رابط المجلد: {str(e)}")
                        return False
            else:
                # رابط عادي
                try:
                    await client(JoinChannelRequest(f'@{group_link}'))
                    return True
                except errors.ChannelInvalidError:
                    logger.error(f"❌ رابط غير صالح: {group_link}")
                    return False
                
        except errors.FloodWaitError as e:
            logger.warning(f"⏳ Flood wait: {e.seconds} ثانية")
            await asyncio.sleep(e.seconds + 1)
            return True
            
        except errors.ChannelPrivateError:
            logger.error(f"🔒 القناة خاصة: {group_link}")
            return False
            
        except errors.InviteHashExpiredError:
            logger.info(f"⏰ رابط منتهي: {group_link}")
            return False
            
        except errors.InviteHashInvalidError:
            logger.error(f"❌ رابط غير صالح: {group_link}")
            return False
            
        except errors.UserAlreadyParticipantError:
            logger.info(f"✅ مستخدم بالفعل في المجموعة: {group_link}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في الانضمام: {str(e)}")
            return False
    
    # ============ واجهات التحكم ============
    
    def start_publishing(self, admin_id):
        """بدء النشر التلقائي"""
        with self.lock:
            if not self.publishing_active.get(admin_id, False):
                self.publishing_active[admin_id] = True
                task = asyncio.create_task(self.publish_to_groups_task(admin_id))
                self.publishing_tasks[admin_id] = task
                logger.info(f"✅ بدأ النشر للمشرف {admin_id}")
                return True
            return False
    
    def stop_publishing(self, admin_id):
        """إيقاف النشر التلقائي"""
        with self.lock:
            if self.publishing_active.get(admin_id, False):
                self.publishing_active[admin_id] = False
                if admin_id in self.publishing_tasks:
                    try:
                        self.publishing_tasks[admin_id].cancel()
                    except:
                        pass
                    del self.publishing_tasks[admin_id]
                logger.info(f"⏹️ توقف النشر للمشرف {admin_id}")
                return True
            return False
    
    def start_private_reply(self, admin_id):
        """بدء الرد على الرسائل الخاصة"""
        with self.lock:
            if not self.private_reply_active.get(admin_id, False):
                self.private_reply_active[admin_id] = True
                task = asyncio.create_task(self.handle_private_messages_task(admin_id))
                self.private_reply_tasks[admin_id] = task
                logger.info(f"✅ بدأ الرد في الخاص للمشرف {admin_id}")
                return True
            return False
    
    def stop_private_reply(self, admin_id):
        """إيقاف الرد على الرسائل الخاصة"""
        with self.lock:
            if self.private_reply_active.get(admin_id, False):
                self.private_reply_active[admin_id] = False
                if admin_id in self.private_reply_tasks:
                    try:
                        self.private_reply_tasks[admin_id].cancel()
                    except:
                        pass
                    del self.private_reply_tasks[admin_id]
                logger.info(f"⏹️ توقف الرد في الخاص للمشرف {admin_id}")
                return True
            return False
    
    def start_group_reply(self, admin_id):
        """بدء الردود في المجموعات"""
        with self.lock:
            if not self.group_reply_active.get(admin_id, False):
                self.group_reply_active[admin_id] = True
                task = asyncio.create_task(self.handle_group_replies_task(admin_id))
                self.group_reply_tasks[admin_id] = task
                logger.info(f"✅ بدأ الرد في القروبات للمشرف {admin_id}")
                return True
            return False
    
    def stop_group_reply(self, admin_id):
        """إيقاف الردود في المجموعات"""
        with self.lock:
            if self.group_reply_active.get(admin_id, False):
                self.group_reply_active[admin_id] = False
                if admin_id in self.group_reply_tasks:
                    try:
                        self.group_reply_tasks[admin_id].cancel()
                    except:
                        pass
                    del self.group_reply_tasks[admin_id]
                logger.info(f"⏹️ توقف الرد في القروبات للمشرف {admin_id}")
                return True
            return False
    
    def start_random_reply(self, admin_id):
        """بدء الردود العشوائية في القروبات"""
        with self.lock:
            if not self.random_reply_active.get(admin_id, False):
                self.random_reply_active[admin_id] = True
                task = asyncio.create_task(self.handle_random_replies_task(admin_id))
                self.random_reply_tasks[admin_id] = task
                logger.info(f"✅ بدأ الرد العشوائي للمشرف {admin_id}")
                return True
            return False
    
    def stop_random_reply(self, admin_id):
        """إيقاف الردود العشوائية في القروبات"""
        with self.lock:
            if self.random_reply_active.get(admin_id, False):
                self.random_reply_active[admin_id] = False
                if admin_id in self.random_reply_tasks:
                    try:
                        self.random_reply_tasks[admin_id].cancel()
                    except:
                        pass
                    del self.random_reply_tasks[admin_id]
                logger.info(f"⏹️ توقف الرد العشوائي للمشرف {admin_id}")
                return True
            return False
    
    def start_join_groups(self, admin_id):
        """بدء الانضمام إلى المجموعات"""
        with self.lock:
            if not self.join_groups_active.get(admin_id, False):
                self.join_groups_active[admin_id] = True
                task = asyncio.create_task(self.join_groups_task(admin_id))
                self.join_groups_tasks[admin_id] = task
                logger.info(f"✅ بدأ الانضمام للمجموعات للمشرف {admin_id}")
                return True
            return False
    
    def stop_join_groups(self, admin_id):
        """إيقاف الانضمام إلى المجموعات"""
        with self.lock:
            if self.join_groups_active.get(admin_id, False):
                self.join_groups_active[admin_id] = False
                if admin_id in self.join_groups_tasks:
                    try:
                        self.join_groups_tasks[admin_id].cancel()
                    except:
                        pass
                    del self.join_groups_tasks[admin_id]
                logger.info(f"⏹️ توقف الانضمام للمجموعات للمشرف {admin_id}")
                return True
            return False
    
    # ============ إحصائيات ============
    
    def get_stats(self):
        """الحصول على الإحصائيات"""
        return {
            'publish_count': self.stats['publish_count'],
            'reply_count': self.stats['reply_count'],
            'join_count': self.stats['join_count'],
            'errors': self.stats['errors'],
            'active_tasks': {
                'publishing': sum(1 for v in self.publishing_active.values() if v),
                'private_reply': sum(1 for v in self.private_reply_active.values() if v),
                'group_reply': sum(1 for v in self.group_reply_active.values() if v),
                'random_reply': sum(1 for v in self.random_reply_active.values() if v),
                'join_groups': sum(1 for v in self.join_groups_active.values() if v)
            },
            'cached_clients': len(self.client_cache)
        }
    
    def reset_stats(self):
        """إعادة تعيين الإحصائيات"""
        self.stats = {
            'publish_count': 0,
            'reply_count': 0,
            'join_count': 0,
            'errors': 0
        }
        logger.info("🔄 تم إعادة تعيين الإحصائيات")
    
    # ============ معالجات الواجهة ============
    
    async def start_publishing_handler(self, query, context):
        """معالج بدء النشر للواجهة"""
        admin_id = query.from_user.id
        
        if self.start_publishing(admin_id):
            stats = self.get_stats()
            await query.edit_message_text(
                f"🚀 **تم بدء النشر!**\n\n"
                f"📊 **الإحصائيات:**\n"
                f"• النشر: {stats['publish_count']}\n"
                f"• الردود: {stats['reply_count']}\n"
                f"• الانضمام: {stats['join_count']}\n"
                f"• الأخطاء: {stats['errors']}\n\n"
                f"⏱️ **تأخير نشر القروبات:** 60 ثانية\n"
                f"⚡ **السرعة:** أقصى ما يمكن",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ النشر يعمل بالفعل!")
    
    async def stop_publishing_handler(self, query, context):
        """معالج إيقاف النشر للواجهة"""
        admin_id = query.from_user.id
        
        if self.stop_publishing(admin_id):
            await query.edit_message_text("⏹️ تم إيقاف النشر!")
        else:
            await query.edit_message_text("⚠️ النشر غير نشط!")
