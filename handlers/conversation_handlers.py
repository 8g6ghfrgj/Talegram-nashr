import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    MessageHandler, 
    filters, 
    CommandHandler,
    CallbackQueryHandler  # ← أضف هذا السطر!
)
from config import (
    ADD_ACCOUNT, ADD_AD_TYPE, ADD_AD_TEXT, ADD_AD_MEDIA,
    ADD_GROUP, ADD_PRIVATE_REPLY, ADD_ADMIN,
    ADD_RANDOM_REPLY, ADD_PRIVATE_TEXT, ADD_GROUP_TEXT,
    ADD_GROUP_PHOTO, MESSAGES
)

logger = logging.getLogger(__name__)

class ConversationHandlers:
    def __init__(self, db, manager, admin_handlers, account_handlers, 
                 ad_handlers, group_handlers, reply_handlers):
        self.db = db
        self.manager = manager
        self.admin_handlers = admin_handlers
        self.account_handlers = account_handlers
        self.ad_handlers = ad_handlers
        self.group_handlers = group_handlers
        self.reply_handlers = reply_handlers
    
    async def handle_callback(self, query, context):
        """معالجة جميع الأزرار العامة"""
        data = query.data
        
        try:
            # أزرار حذف الحسابات
            if data.startswith("delete_account_"):
                account_id = int(data.replace("delete_account_", ""))
                await self.account_handlers.delete_account(query, context, account_id)
            
            # أزرار تبديل حالة الحسابات
            elif data.startswith("toggle_account_"):
                account_id = int(data.replace("toggle_account_", ""))
                await self.account_handlers.toggle_account_status(query, context, account_id)
            
            # أزرار إحصائيات الحسابات
            elif data == "account_stats":
                await self.account_handlers.show_account_stats(query, context)
            
            # أزرار حذف الإعلانات
            elif data.startswith("delete_ad_"):
                ad_id = int(data.replace("delete_ad_", ""))
                await self.ad_handlers.delete_ad(query, context, ad_id)
            
            # أزرار إحصائيات الإعلانات
            elif data == "ad_stats":
                await self.ad_handlers.show_ad_stats(query, context)
            
            # أزرار حذف المجموعات
            elif data.startswith("delete_group_"):
                group_id = int(data.replace("delete_group_", ""))
                await self.group_handlers.delete_group(query, context, group_id)
            
            # أزرار تحديث المجموعات
            elif data.startswith("update_group_"):
                group_id = int(data.replace("update_group_", ""))
                await self.update_group_status(query, context, group_id)
            
            # أزرار إحصائيات المجموعات
            elif data == "group_stats":
                await self.group_handlers.show_group_stats(query, context)
            
            # أزرار حذف المشرفين
            elif data.startswith("delete_admin_"):
                admin_id = int(data.replace("delete_admin_", ""))
                await self.admin_handlers.delete_admin(query, context, admin_id)
            
            # أزرار تبديل حالة المشرفين
            elif data.startswith("toggle_admin_"):
                admin_id = int(data.replace("toggle_admin_", ""))
                await self.admin_handlers.toggle_admin_status(query, context, admin_id)
            
            # أزرار إحصائيات النظام
            elif data == "system_stats":
                await self.admin_handlers.show_system_stats(query, context)
            
            # أزرار تصدير البيانات
            elif data == "export_data":
                await self.admin_handlers.export_data(query, context)
            
            # أزرار حذف الردود الخاصة
            elif data.startswith("delete_private_reply_"):
                reply_id = int(data.replace("delete_private_reply_", ""))
                await self.reply_handlers.delete_private_reply(query, context, reply_id)
            
            # أزرار حذف الردود النصية
            elif data.startswith("delete_text_reply_"):
                reply_id = int(data.replace("delete_text_reply_", ""))
                await self.delete_text_reply(query, context, reply_id)
            
            # أزرار حذف الردود مع الصور
            elif data.startswith("delete_photo_reply_"):
                reply_id = int(data.replace("delete_photo_reply_", ""))
                await self.delete_photo_reply(query, context, reply_id)
            
            # أزرار حذف الردود العشوائية
            elif data.startswith("delete_random_reply_"):
                reply_id = int(data.replace("delete_random_reply_", ""))
                await self.delete_random_reply(query, context, reply_id)
            
            # أزرار عرض الردود للحذف
            elif data == "show_private_replies_delete":
                await self.reply_handlers.show_private_replies_delete(query, context)
            
            elif data == "show_text_replies_delete":
                await self.show_text_replies_delete(query, context)
            
            elif data == "show_photo_replies_delete":
                await self.show_photo_replies_delete(query, context)
            
            elif data == "show_random_replies_delete":
                await self.show_random_replies_delete(query, context)
            
            # أزرار بدء/إيقاف المهام
            elif data == "stop_private_reply":
                await self.reply_handlers.stop_private_reply(query, context)
            
            elif data == "stop_group_reply":
                await self.stop_group_reply(query, context)
            
            elif data == "stop_random_reply":
                await self.stop_random_reply(query, context)
            
            elif data == "stop_join_groups":
                await self.group_handlers.stop_join_groups(query, context)
            
            # أزرار النشر
            elif data == "start_private_reply":
                await self.reply_handlers.start_private_reply(query, context)
            
            elif data == "start_group_reply":
                await self.start_group_reply(query, context)
            
            elif data == "start_random_reply":
                await self.start_random_reply(query, context)
            
            elif data == "start_join_groups":
                await self.group_handlers.start_join_groups(query, context)
            
            # أزرار الإدارة
            elif data == "private_replies":
                await self.reply_handlers.manage_private_replies(query, context)
            
            elif data == "group_replies":
                await self.reply_handlers.manage_group_replies(query, context)
            
            elif data == "show_replies":
                await self.reply_handlers.show_replies_menu(query, context)
            
            # أزرار أخرى
            elif data == "add_account":
                await self.account_handlers.add_account_start(query.update, context)
            
            elif data == "show_accounts":
                await self.account_handlers.show_accounts(query, context)
            
            elif data == "add_ad":
                await self.ad_handlers.add_ad_start(query, context)
            
            elif data == "show_ads":
                await self.ad_handlers.show_ads(query, context)
            
            elif data == "add_group":
                await self.group_handlers.add_group_start(query.update, context)
            
            elif data == "show_groups":
                await self.group_handlers.show_groups(query, context)
            
            elif data == "add_admin":
                await self.admin_handlers.add_admin_start(query.update, context)
            
            elif data == "show_admins":
                await self.admin_handlers.show_admins(query, context)
            
            elif data == "add_private_reply":
                await self.reply_handlers.add_private_reply_start(query.update, context)
            
            elif data == "add_group_text_reply":
                await self.reply_handlers.add_group_text_reply_start(query.update, context)
            
            elif data == "add_group_photo_reply":
                await self.reply_handlers.add_group_photo_reply_start(query.update, context)
            
            elif data == "add_random_reply":
                await self.reply_handlers.add_random_reply_start(query.update, context)
            
            else:
                # إذا لم يتم التعرف على الزر
                await query.edit_message_text(
                    "❌ أمر غير معروف!\n"
                    "استخدم الأزرار المتاحة فقط."
                )
                
        except ValueError as e:
            logger.error(f"خطأ في تحويل الرقم: {e}")
            await query.edit_message_text("❌ خطأ في معالجة الأمر!")
        except Exception as e:
            logger.error(f"خطأ في معالجة الزر {data}: {e}")
            await query.edit_message_text(f"❌ خطأ في معالجة الأمر: {str(e)}")
    
    async def handle_back_buttons(self, query, context, data):
        """معالجة أزرار الرجوع"""
        if data == "back_to_main":
            await self.show_main_menu(query, context)
        elif data == "back_to_accounts":
            await self.account_handlers.manage_accounts(query, context)
        elif data == "back_to_ads":
            await self.ad_handlers.manage_ads(query, context)
        elif data == "back_to_groups":
            await self.group_handlers.manage_groups(query, context)
        elif data == "back_to_replies":
            await self.reply_handlers.manage_replies(query, context)
        elif data == "back_to_admins":
            await self.admin_handlers.manage_admins(query, context)
        elif data == "back_to_private_replies":
            await self.reply_handlers.manage_private_replies(query, context)
        elif data == "back_to_group_replies":
            await self.reply_handlers.manage_group_replies(query, context)
    
    async def show_main_menu(self, query, context):
        """عرض القائمة الرئيسية"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        keyboard = [
            [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="manage_ads")],
            [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
            [InlineKeyboardButton("💬 إدارة الردود", callback_data="manage_replies")],
            [InlineKeyboardButton("👨‍💼 إدارة المشرفين", callback_data="manage_admins")],
            [InlineKeyboardButton("🚀 بدء النشر", callback_data="start_publishing")],
            [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_publishing")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            MESSAGES['start'],
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def update_group_status(self, query, context, group_id):
        """تحديث حالة مجموعة"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        # تغيير الحالة من pending إلى joined والعكس
        conn = self.db.conn if hasattr(self.db, 'conn') else None
        if not conn:
            import sqlite3
            conn = sqlite3.connect(self.db.db_name)
        
        cursor = conn.cursor()
        
        try:
            # الحصول على الحالة الحالية
            cursor.execute('SELECT status FROM groups WHERE id = ?', (group_id,))
            result = cursor.fetchone()
            
            if not result:
                await query.edit_message_text(f"❌ المجموعة #{group_id} غير موجودة!")
                return
            
            current_status = result[0]
            new_status = 'joined' if current_status == 'pending' else 'pending'
            
            # تحديث الحالة
            cursor.execute('''
                UPDATE groups 
                SET status = ?, join_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, group_id))
            conn.commit()
            
            status_text = "منضمة" if new_status == 'joined' else "معلقة"
            await query.edit_message_text(f"✅ تم تغيير حالة المجموعة #{group_id} إلى: {status_text}")
            
        except Exception as e:
            logger.error(f"خطأ في تحديث حالة المجموعة: {e}")
            await query.edit_message_text(f"❌ خطأ في تحديث الحالة: {str(e)}")
        finally:
            if conn:
                conn.close()
        
        await self.group_handlers.show_groups(query, context)
    
    async def delete_text_reply(self, query, context, reply_id):
        """حذف رد نصي"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        if self.db.delete_group_text_reply(reply_id, user_id):
            await query.edit_message_text(f"✅ تم حذف الرد النصي #{reply_id} بنجاح")
        else:
            await query.edit_message_text(
                f"❌ فشل حذف الرد النصي #{reply_id}\n"
                "قد يكون الرد غير موجود أو ليس لديك صلاحية لحذفه."
            )
        
        await self.show_text_replies_delete(query, context)
    
    async def delete_photo_reply(self, query, context, reply_id):
        """حذف رد مع صورة"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        if self.db.delete_group_photo_reply(reply_id, user_id):
            await query.edit_message_text(f"✅ تم حذف الرد مع الصورة #{reply_id} بنجاح")
        else:
            await query.edit_message_text(
                f"❌ فشل حذف الرد مع الصورة #{reply_id}\n"
                "قد يكون الرد غير موجود أو ليس لديك صلاحية لحذفه."
            )
        
        await self.show_photo_replies_delete(query, context)
    
    async def delete_random_reply(self, query, context, reply_id):
        """حذف رد عشوائي"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        if self.db.delete_group_random_reply(reply_id, user_id):
            await query.edit_message_text(f"✅ تم حذف الرد العشوائي #{reply_id} بنجاح")
        else:
            await query.edit_message_text(
                f"❌ فشل حذف الرد العشوائي #{reply_id}\n"
                "قد يكون الرد غير موجود أو ليس لديك صلاحية لحذفه."
            )
        
        await self.show_random_replies_delete(query, context)
    
    async def show_text_replies_delete(self, query, context):
        """عرض الردود النصية للحذف"""
        user_id = query.from_user.id
        replies = self.db.get_group_text_replies(user_id)
        
        if not replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود نصية مضافة",
                reply_markup=reply_markup
            )
            return
        
        text = "🗑️ **الردود النصية في القروبات للحذف:**\n\n"
        
        keyboard = []
        
        for reply in replies[:15]:
            reply_id, trigger, reply_text, is_active, added_date, reply_admin_id, is_encoded = reply
            
            text += f"**#{reply_id}** - {trigger}\n"
            text += f"➡️ {reply_text[:30]}...\n"
            text += f"الحالة: {'🟢 نشط' if is_active else '🔴 غير نشط'}\n"
            text += "─" * 20 + "\n"
            
            keyboard.append([InlineKeyboardButton(f"🗑️ حذف #{reply_id}", callback_data=f"delete_text_reply_{reply_id}")])
        
        if len(replies) > 15:
            text += f"\n... وعرض {len(replies) - 15} رد إضافي"
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث القائمة", callback_data="show_text_replies_delete"),
            InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_photo_replies_delete(self, query, context):
        """عرض الردود مع الصور للحذف"""
        user_id = query.from_user.id
        replies = self.db.get_group_photo_replies(user_id)
        
        if not replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود مع صور مضافة",
                reply_markup=reply_markup
            )
            return
        
        text = "🗑️ **الردود مع الصور في القروبات للحذف:**\n\n"
        
        keyboard = []
        
        for reply in replies[:15]:
            reply_id, trigger, reply_text, media_path, is_active, added_date, reply_admin_id, is_encoded = reply
            
            text += f"**#{reply_id}** - {trigger}\n"
            text += f"➡️ {reply_text[:30] if reply_text else 'بدون نص'}...\n"
            text += f"🖼️ مع صورة\n"
            text += f"الحالة: {'🟢 نشط' if is_active else '🔴 غير نشط'}\n"
            text += "─" * 20 + "\n"
            
            keyboard.append([InlineKeyboardButton(f"🗑️ حذف #{reply_id}", callback_data=f"delete_photo_reply_{reply_id}")])
        
        if len(replies) > 15:
            text += f"\n... وعرض {len(replies) - 15} رد إضافي"
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث القائمة", callback_data="show_photo_replies_delete"),
            InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_random_replies_delete(self, query, context):
        """عرض الردود العشوائية للحذف"""
        user_id = query.from_user.id
        replies = self.db.get_group_random_replies(user_id)
        
        if not replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود عشوائية مضافة",
                reply_markup=reply_markup
            )
            return
        
        text = "🗑️ **الردود العشوائية في القروبات للحذف:**\n\n"
        
        keyboard = []
        
        for reply in replies[:15]:
            reply_id, reply_text, media_path, is_active, added_date, reply_admin_id, is_encoded, has_media = reply
            
            text += f"**#{reply_id}**\n"
            text += f"🎲 {reply_text[:50] if reply_text else 'رد عشوائي'}...\n"
            text += f"🖼️ {'مع صورة' if has_media else 'نص فقط'}\n"
            text += f"الحالة: {'🟢 نشط' if is_active else '🔴 غير نشط'}\n"
            text += "─" * 20 + "\n"
            
            keyboard.append([InlineKeyboardButton(f"🗑️ حذف #{reply_id}", callback_data=f"delete_random_reply_{reply_id}")])
        
        if len(replies) > 15:
            text += f"\n... وعرض {len(replies) - 15} رد إضافي"
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث القائمة", callback_data="show_random_replies_delete"),
            InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def start_group_reply(self, query, context):
        """بدء الرد التلقائي في القروبات"""
        admin_id = query.from_user.id
        
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد حسابات نشطة!",
                reply_markup=reply_markup
            )
            return
        
        text_replies = self.db.get_group_text_replies(admin_id)
        photo_replies = self.db.get_group_photo_replies(admin_id)
        
        if not text_replies and not photo_replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود مضافة!",
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_group_reply(admin_id):
            keyboard = [[InlineKeyboardButton("⏹️ إيقاف الرد", callback_data="stop_group_reply")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👥 **تم بدء الرد في القروبات بأقصى سرعة!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **عدد الردود النصية:** {len(text_replies)}\n"
                f"✅ **عدد الردود مع الصور:** {len(photo_replies)}\n"
                f"⚡ **بين الردود:** 0.05 ثانية\n"
                f"⚡ **بين الدورات:** 3 ثواني\n\n"
                "سيبدأ البوت بالرد على الرسائل في القروبات الآن بأقصى سرعة ممكنة.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ الرد في القروبات يعمل بالفعل!")
    
    async def stop_group_reply(self, query, context):
        """إيقاف الرد التلقائي في القروبات"""
        admin_id = query.from_user.id
        
        if self.manager.stop_group_reply(admin_id):
            await query.edit_message_text("⏹️ تم إيقاف الرد في القروبات!")
        else:
            await query.edit_message_text("⚠️ الرد في القروبات غير نشط!")
    
    async def start_random_reply(self, query, context):
        """بدء الردود العشوائية في القروبات"""
        admin_id = query.from_user.id
        
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد حسابات نشطة!",
                reply_markup=reply_markup
            )
            return
        
        random_replies = self.db.get_group_random_replies(admin_id)
        if not random_replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود عشوائية مضافة!",
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_random_reply(admin_id):
            keyboard = [[InlineKeyboardButton("⏹️ إيقاف الرد العشوائي", callback_data="stop_random_reply")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🎲 **تم بدء الردود العشوائية بأقصى سرعة!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **عدد الردود العشوائية:** {len(random_replies)}\n"
                f"✅ **الرد على 100% من الرسائل**\n"
                f"⚡ **بين الردود:** 0.05 ثانية\n"
                f"⚡ **بين الدورات:** 3 ثواني\n\n"
                "سيبدأ البوت بالرد العشوائي في القروبات الآن بأقصى سرعة ممكنة.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ الرد العشوائي يعمل بالفعل!")
    
    async def stop_random_reply(self, query, context):
        """إيقاف الردود العشوائية في القروبات"""
        admin_id = query.from_user.id
        
        if self.manager.stop_random_reply(admin_id):
            await query.edit_message_text("⏹️ تم إيقاف الرد العشوائي!")
        else:
            await query.edit_message_text("⚠️ الرد العشوائي غير نشط!")
    
    async def start_publishing(self, query, context):
        """بدء النشر التلقائي"""
        admin_id = query.from_user.id
        
        # التحقق من وجود حسابات
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                MESSAGES['no_accounts'],
                reply_markup=reply_markup
            )
            return
        
        # التحقق من وجود إعلانات
        ads = self.db.get_ads(admin_id)
        if not ads:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                MESSAGES['no_ads'],
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_publishing(admin_id):
            keyboard = [
                [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_publishing")],
                [InlineKeyboardButton("💬 بدء الرد في الخاص", callback_data="start_private_reply")],
                [InlineKeyboardButton("👥 بدء الرد في القروبات", callback_data="start_group_reply")],
                [InlineKeyboardButton("🎲 بدء الرد العشوائي", callback_data="start_random_reply")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🚀 **تم بدء النشر بأقصى سرعة!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **عدد الإعلانات:** {len(ads)}\n"
                f"⏱️ **تأخير نشر القروبات:** 60 ثانية\n"
                f"⚡ **بين الإعلانات:** 0.1 ثانية\n"
                f"⚡ **بين المجموعات:** 0.2 ثانية\n"
                f"⚡ **بين الدورات:** 30 ثانية\n\n"
                "سيبدأ البوت بالنشر في جميع المجموعات الآن مع تأمين الحسابات.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ النشر يعمل بالفعل!")
    
    async def stop_publishing(self, query, context):
        """إيقاف النشر التلقائي"""
        admin_id = query.from_user.id
        
        if self.manager.stop_publishing(admin_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⏹️ تم إيقاف النشر!", reply_markup=reply_markup)
        else:
            await query.edit_message_text("⚠️ النشر غير نشط!")
    
    def setup_conversation_handlers(self, application):
        """إعداد معالجات المحادثة"""
        # محادثة إضافة الحساب
        add_account_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.account_handlers.add_account_start, 
                pattern="^add_account$"
            )],
            states={
                ADD_ACCOUNT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        self.account_handlers.add_account_session
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        application.add_handler(add_account_conv)
        
        # محادثة إضافة الإعلان
        add_ad_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.ad_handlers.add_ad_type,
                pattern="^ad_type_"
            )],
            states={
                ADD_AD_TEXT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.ad_handlers.add_ad_text
                    )
                ],
                ADD_AD_MEDIA: [
                    MessageHandler(filters.PHOTO, self.ad_handlers.add_ad_media),
                    MessageHandler(filters.Document.ALL, self.ad_handlers.add_ad_media),
                    MessageHandler(filters.CONTACT, self.ad_handlers.add_ad_media)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        application.add_handler(add_ad_conv)
        
        # محادثة إضافة المجموعة
        add_group_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.group_handlers.add_group_start,
                pattern="^add_group$"
            )],
            states={
                ADD_GROUP: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.group_handlers.add_group_link
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        application.add_handler(add_group_conv)
        
        # محادثة إضافة المشرف
        add_admin_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.admin_handlers.add_admin_start,
                pattern="^add_admin$"
            )],
            states={
                ADD_ADMIN: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.admin_handlers.add_admin_id
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        application.add_handler(add_admin_conv)
        
        # محادثة إضافة رد خاص
        private_reply_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.reply_handlers.add_private_reply_start,
                pattern="^add_private_reply$"
            )],
            states={
                ADD_PRIVATE_TEXT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.reply_handlers.add_private_reply_text
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        application.add_handler(private_reply_conv)
        
        # محادثة إضافة رد نصي في القروبات
        group_text_reply_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.reply_handlers.add_group_text_reply_start,
                pattern="^add_group_text_reply$"
            )],
            states={
                ADD_GROUP_TEXT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.reply_handlers.add_group_text_reply_trigger
                    ),
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.reply_handlers.add_group_text_reply_text
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )
        application.add_handler(group_text_reply_conv)
        
        # محادثة إضافة رد مع صورة في القروبات
        group_photo_reply_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.reply_handlers.add_group_photo_reply_start,
                pattern="^add_group_photo_reply$"
            )],
            states={
                ADD_GROUP_PHOTO: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.reply_handlers.add_group_photo_reply_trigger
                    ),
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.reply_handlers.add_group_photo_reply_text
                    ),
                    MessageHandler(
                        filters.PHOTO,
                        self.reply_handlers.add_group_photo_reply_photo
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        application.add_handler(group_photo_reply_conv)
        
        # محادثة إضافة رد عشوائي
        random_reply_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.reply_handlers.add_random_reply_start,
                pattern="^add_random_reply$"
            )],
            states={
                ADD_RANDOM_REPLY: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.reply_handlers.add_random_reply_text
                    ),
                    MessageHandler(
                        filters.PHOTO,
                        self.reply_handlers.add_random_reply_media
                    ),
                    CommandHandler("skip", self.reply_handlers.skip_random_reply_media)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        application.add_handler(random_reply_conv)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء الأمر الحالي"""
        user_id = update.message.from_user.id
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        await update.message.reply_text("❌ تم إلغاء الأمر.")
        return ConversationHandler.END
