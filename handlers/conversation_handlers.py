import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackQueryHandler
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
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة جميع الأزرار العامة"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        # التحقق من صلاحية المستخدم
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية للوصول إلى هذا البوت.")
            return
        
        logger.info(f"معالجة الزر: {data} للمستخدم: {user_id}")
        
        try:
            # معالجة أزرار الرجوع أولاً
            if data.startswith("back_to_"):
                await self.handle_back_buttons(query, context, data)
                return
            
            # أزرار إدارة الحسابات
            elif data == "manage_accounts":
                await self.account_handlers.manage_accounts(query, context)
            elif data == "add_account":
                await self.account_handlers.add_account_start(update, context)
            elif data == "show_accounts":
                await self.account_handlers.show_accounts(query, context)
            elif data.startswith("delete_account_"):
                try:
                    account_id = int(data.split("_")[-1])
                    await self.account_handlers.delete_account(query, context, account_id)
                except (ValueError, IndexError) as e:
                    logger.error(f"خطأ في استخراج account_id من {data}: {e}")
                    await query.edit_message_text("❌ خطأ في معالجة الأمر!")
            
            # أزرار إدارة الإعلانات
            elif data == "manage_ads":
                await self.ad_handlers.manage_ads(query, context)
            elif data == "add_ad":
                await self.ad_handlers.add_ad_start(query, context)
            elif data == "show_ads":
                await self.ad_handlers.show_ads(query, context)
            elif data.startswith("delete_ad_"):
                try:
                    ad_id = int(data.split("_")[-1])
                    await self.ad_handlers.delete_ad(query, context, ad_id)
                except (ValueError, IndexError) as e:
                    logger.error(f"خطأ في استخراج ad_id من {data}: {e}")
                    await query.edit_message_text("❌ خطأ في معالجة الأمر!")
            
            # أزرار إدارة المجموعات
            elif data == "manage_groups":
                await self.group_handlers.manage_groups(query, context)
            elif data == "add_group":
                await self.group_handlers.add_group_start(update, context)
            elif data == "show_groups":
                await self.group_handlers.show_groups(query, context)
            elif data == "start_join_groups":
                await self.group_handlers.start_join_groups(query, context)
            
            # أزرار إدارة المشرفين
            elif data == "manage_admins":
                await self.admin_handlers.manage_admins(query, context)
            elif data == "add_admin":
                await self.admin_handlers.add_admin_start(update, context)
            elif data == "show_admins":
                await self.admin_handlers.show_admins(query, context)
            elif data.startswith("delete_admin_"):
                try:
                    admin_id = int(data.split("_")[-1])
                    await self.admin_handlers.delete_admin(query, context, admin_id)
                except (ValueError, IndexError) as e:
                    logger.error(f"خطأ في استخراج admin_id من {data}: {e}")
                    await query.edit_message_text("❌ خطأ في معالجة الأمر!")
            
            # أزرار إدارة الردود
            elif data == "manage_replies":
                await self.reply_handlers.manage_replies(query, context)
            elif data == "private_replies":
                await self.reply_handlers.manage_private_replies(query, context)
            elif data == "group_replies":
                await self.reply_handlers.manage_group_replies(query, context)
            elif data == "show_replies":
                await self.reply_handlers.show_replies_menu(query, context)
            elif data == "add_private_reply":
                await self.reply_handlers.add_private_reply_start(update, context)
            elif data == "add_group_text_reply":
                await self.reply_handlers.add_group_text_reply_start(update, context)
            elif data == "add_group_photo_reply":
                await self.reply_handlers.add_group_photo_reply_start(update, context)
            elif data == "add_random_reply":
                await self.reply_handlers.add_random_reply_start(update, context)
            
            # أزرار حذف الردود
            elif data == "show_private_replies_delete":
                await self.reply_handlers.show_private_replies_delete(query, context)
            elif data == "show_text_replies_delete":
                await self.reply_handlers.show_text_replies_delete(query, context)
            elif data == "show_photo_replies_delete":
                await self.reply_handlers.show_photo_replies_delete(query, context)
            elif data == "show_random_replies_delete":
                await self.reply_handlers.show_random_replies_delete(query, context)
            
            # أزرار النشر
            elif data == "start_publishing":
                await self.start_publishing(query, context)
            elif data == "stop_publishing":
                await self.stop_publishing(query, context)
            
            # أزرار الرد الخاص
            elif data == "start_private_reply":
                await self.reply_handlers.start_private_reply(query, context)
            elif data == "stop_private_reply":
                await self.reply_handlers.stop_private_reply(query, context)
            
            # أزرار الرد الجماعي
            elif data == "start_group_reply":
                await self.reply_handlers.start_group_reply(query, context)
            elif data == "stop_group_reply":
                await self.reply_handlers.stop_group_reply(query, context)
            
            # أزرار الرد العشوائي
            elif data == "start_random_reply":
                await self.reply_handlers.start_random_reply(query, context)
            elif data == "stop_random_reply":
                await self.reply_handlers.stop_random_reply(query, context)
            
            # أزرار أنواع الإعلانات
            elif data.startswith("ad_type_"):
                ad_type = data.replace("ad_type_", "")
                await self.ad_handlers.handle_ad_type(query, context, ad_type)
            
            # الأزرار غير المعروفة
            else:
                await query.edit_message_text(
                    "❌ أمر غير معروف!\n"
                    "استخدم الأزرار المتاحة فقط."
                )
                
        except Exception as e:
            logger.error(f"خطأ في معالجة الزر {data}: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ حدث خطأ غير متوقع في النظام.\n"
                "الرجاء المحاولة مرة أخرى أو الاتصال بالمطور."
            )
    
    async def handle_back_buttons(self, query, context, data):
        """معالجة أزرار الرجوع"""
        try:
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
        except Exception as e:
            logger.error(f"خطأ في معالجة زر الرجوع {data}: {e}")
            await query.edit_message_text("❌ خطأ في معالجة أمر الرجوع!")
    
    async def show_main_menu(self, query, context):
        """عرض القائمة الرئيسية"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية للوصول إلى هذا البوت.")
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
            "🚀 لوحة تحكم البوت الفعلي - السرعة القصوى\n\n"
            "⚡ النشر بأقصى سرعة ممكنة\n"
            "⚡ الردود التلقائية بأقصى سرعة\n"
            "⚡ الانضمام للمجموعات بأقصى سرعة\n\n"
            "اختر الإجراء الذي تريد تنفيذه:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_publishing(self, query, context):
        """بدء النشر التلقائي"""
        try:
            admin_id = query.from_user.id
            
            # التحقق من وجود حسابات
            accounts = self.db.get_active_publishing_accounts(admin_id)
            if not accounts:
                keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ لا توجد حسابات نشطة!\n\n"
                    "يجب إضافة حسابات أولاً قبل بدء النشر.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            
            # التحقق من وجود إعلانات
            ads = self.db.get_ads(admin_id)
            if not ads:
                keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ لا توجد إعلانات!\n\n"
                    "يجب إضافة إعلانات أولاً قبل بدء النشر.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
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
                logger.info(f"✅ بدأ النشر للمشرف {admin_id}")
            else:
                await query.edit_message_text("⚠️ النشر يعمل بالفعل!")
                
        except Exception as e:
            logger.error(f"خطأ في بدء النشر: {e}")
            await query.edit_message_text(
                "❌ حدث خطأ في بدء النشر.\n"
                "الرجاء المحاولة مرة أخرى."
            )
    
    async def stop_publishing(self, query, context):
        """إيقاف النشر التلقائي"""
        try:
            admin_id = query.from_user.id
            
            if self.manager.stop_publishing(admin_id):
                keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("⏹️ تم إيقاف النشر!", reply_markup=reply_markup)
                logger.info(f"⏹️ توقف النشر للمشرف {admin_id}")
            else:
                await query.edit_message_text("⚠️ النشر غير نشط!")
                
        except Exception as e:
            logger.error(f"خطأ في إيقاف النشر: {e}")
            await query.edit_message_text("❌ حدث خطأ في إيقاف النشر.")
    
    def setup_conversation_handlers(self, application):
        """إعداد معالجات المحادثة"""
        # معالج الأزرار الرئيسي
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # محادثة إضافة الحساب
        from config import ADD_ACCOUNT
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
        from config import ADD_AD_TEXT, ADD_AD_MEDIA
        add_ad_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.ad_handlers.handle_ad_type,
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
        from config import ADD_GROUP
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
        from config import ADD_ADMIN
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
        from config import ADD_PRIVATE_TEXT
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
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء الأمر الحالي"""
        try:
            user_id = update.message.from_user.id
            if not self.db.is_admin(user_id):
                await update.message.reply_text("❌ ليس لديك صلاحية للوصول إلى هذا البوت.")
                return ConversationHandler.END
            
            await update.message.reply_text("❌ تم إلغاء الأمر.")
            await self.show_main_menu_for_user(user_id, update.message.chat_id, context)
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"خطأ في إلغاء الأمر: {e}")
            return ConversationHandler.END
    
    async def show_main_menu_for_user(self, user_id, chat_id, context):
        """عرض القائمة الرئيسية لمستخدم معين"""
        try:
            if not self.db.is_admin(user_id):
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
            
            await context.bot.send_message(
                chat_id=chat_id,
                text="🚀 لوحة تحكم البوت الفعلي - السرعة القصوى\n\n"
                     "⚡ النشر بأقصى سرعة ممكنة\n"
                     "⚡ الردود التلقائية بأقصى سرعة\n"
                     "⚡ الانضمام للمجموعات بأقصى سرعة\n\n"
                     "اختر الإجراء الذي تريد تنفيذه:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في عرض القائمة الرئيسية: {e}")
