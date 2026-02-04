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

    # ==========================================================
    # MAIN CALLBACK HANDLER
    # ==========================================================

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية.")
            return

        try:

            # -------- BACK BUTTONS --------

            if data.startswith("back_to_"):
                await self.handle_back_buttons(query, context)
                return

            # -------- ACCOUNTS --------

            if data == "manage_accounts":
                await self.account_handlers.manage_accounts(query, context)

            elif data == "show_accounts":
                await self.account_handlers.show_accounts(query, context)

            elif data.startswith("delete_account_"):
                account_id = int(data.replace("delete_account_", ""))
                await self.account_handlers.delete_account(query, context, account_id)

            # -------- ADS --------

            elif data == "manage_ads":
                await self.ad_handlers.manage_ads(query, context)

            elif data == "show_ads":
                await self.ad_handlers.show_ads(query, context)

            elif data == "ad_stats":
                await self.ad_handlers.show_ad_stats(query, context)

            elif data.startswith("delete_ad_"):
                ad_id = int(data.replace("delete_ad_", ""))
                await self.ad_handlers.delete_ad(query, context, ad_id)

            # -------- GROUPS --------

            elif data == "manage_groups":
                await self.group_handlers.manage_groups(query, context)

            elif data == "show_groups":
                await self.group_handlers.show_groups(query, context)

            elif data == "start_join_groups":
                await self.group_handlers.start_join_groups(query, context)

            elif data == "stop_join_groups":
                await self.group_handlers.stop_join_groups(query, context)

            # -------- ADMINS --------

            elif data == "manage_admins":
                await self.admin_handlers.manage_admins(query, context)

            elif data == "show_admins":
                await self.admin_handlers.show_admins(query, context)

            elif data.startswith("delete_admin_"):
                admin_id = int(data.replace("delete_admin_", ""))
                await self.admin_handlers.delete_admin(query, context, admin_id)

            elif data.startswith("toggle_admin_"):
                admin_id = int(data.replace("toggle_admin_", ""))
                await self.admin_handlers.toggle_admin_status(query, context, admin_id)

            elif data == "system_stats":
                await self.admin_handlers.show_system_stats(query, context)

            elif data == "export_data":
                await self.admin_handlers.export_data(query, context)

            # -------- REPLIES --------

            elif data == "manage_replies":
                await self.reply_handlers.manage_replies(query, context)

            elif data == "private_replies":
                await self.reply_handlers.manage_private_replies(query, context)

            elif data == "group_replies":
                await self.reply_handlers.manage_group_replies(query, context)

            elif data == "show_replies":
                await self.reply_handlers.show_replies_menu(query, context)

            elif data.startswith("delete_private_reply_"):
                reply_id = int(data.replace("delete_private_reply_", ""))
                await self.reply_handlers.delete_private_reply(query, context, reply_id)

            elif data.startswith("delete_text_reply_"):
                reply_id = int(data.replace("delete_text_reply_", ""))
                await self.reply_handlers.delete_text_reply(query, context, reply_id)

            elif data.startswith("delete_photo_reply_"):
                reply_id = int(data.replace("delete_photo_reply_", ""))
                await self.reply_handlers.delete_photo_reply(query, context, reply_id)

            elif data.startswith("delete_random_reply_"):
                reply_id = int(data.replace("delete_random_reply_", ""))
                await self.reply_handlers.delete_random_reply(query, context, reply_id)

            # -------- PUBLISHING --------

            elif data == "start_publishing":
                await self.start_publishing(query, context)

            elif data == "stop_publishing":
                await self.stop_publishing(query, context)

            elif data == "start_private_reply":
                await self.reply_handlers.start_private_reply(query, context)

            elif data == "stop_private_reply":
                await self.reply_handlers.stop_private_reply(query, context)

            elif data == "start_group_reply":
                await self.reply_handlers.start_group_reply(query, context)

            elif data == "stop_group_reply":
                await self.reply_handlers.stop_group_reply(query, context)

            elif data == "start_random_reply":
                await self.reply_handlers.start_random_reply(query, context)

            elif data == "stop_random_reply":
                await self.reply_handlers.stop_random_reply(query, context)

            else:
                await query.edit_message_text("❌ زر غير معروف.")

        except Exception as e:
            logger.error(f"Callback error {data}: {e}", exc_info=True)
            await query.edit_message_text("❌ خطأ في النظام.")

    # ==========================================================
    # BACK BUTTONS
    # ==========================================================

    async def handle_back_buttons(self, query, context):

        data = query.data

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

    # ==========================================================
    # MAIN MENU
    # ==========================================================

    async def show_main_menu(self, query, context):

        keyboard = [
            [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="manage_ads")],
            [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
            [InlineKeyboardButton("💬 إدارة الردود", callback_data="manage_replies")],
            [InlineKeyboardButton("👨‍💼 إدارة المشرفين", callback_data="manage_admins")],
            [InlineKeyboardButton("🚀 بدء النشر", callback_data="start_publishing")],
            [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_publishing")]
        ]

        await query.edit_message_text(
            "🚀 لوحة التحكم الرئيسية",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==========================================================
    # PUBLISHING
    # ==========================================================

    async def start_publishing(self, query, context):

        admin_id = query.from_user.id

        accounts = self.db.get_active_publishing_accounts(admin_id)
        ads = self.db.get_ads(admin_id)

        if not accounts:
            await query.edit_message_text("❌ لا توجد حسابات نشطة.")
            return

        if not ads:
            await query.edit_message_text("❌ لا توجد إعلانات.")
            return

        if self.manager.start_publishing(admin_id):
            await query.edit_message_text("🚀 تم بدء النشر.")
        else:
            await query.edit_message_text("⚠️ النشر يعمل بالفعل.")

    async def stop_publishing(self, query, context):

        admin_id = query.from_user.id

        if self.manager.stop_publishing(admin_id):
            await query.edit_message_text("⏹️ تم إيقاف النشر.")
        else:
            await query.edit_message_text("⚠️ النشر غير نشط.")

    # ==========================================================
    # SETUP HANDLERS (IMPORTANT ORDER)
    # ==========================================================

    def setup_conversation_handlers(self, application):

        from config import (
            ADD_ACCOUNT, ADD_AD_TEXT, ADD_AD_MEDIA, ADD_GROUP,
            ADD_ADMIN, ADD_PRIVATE_TEXT, ADD_GROUP_TEXT,
            ADD_GROUP_PHOTO, ADD_RANDOM_REPLY
        )

        # -------- ADD ACCOUNT --------
        application.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(
                    self.account_handlers.add_account_start,
                    pattern="^add_account$"
                )],
                states={
                    ADD_ACCOUNT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       self.account_handlers.add_account_session)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel)]
            )
        )

        # -------- ADD AD --------
        application.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(
                    self.ad_handlers.add_ad_type,
                    pattern="^ad_type_"
                )],
                states={
                    ADD_AD_TEXT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       self.ad_handlers.add_ad_text)
                    ],
                    ADD_AD_MEDIA: [
                        MessageHandler(filters.PHOTO | filters.Document.ALL | filters.CONTACT,
                                       self.ad_handlers.add_ad_media)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel)]
            )
        )

        # -------- ADD GROUP --------
        application.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(
                    self.group_handlers.add_group_start,
                    pattern="^add_group$"
                )],
                states={
                    ADD_GROUP: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       self.group_handlers.add_group_link)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel)]
            )
        )

        # -------- ADD ADMIN --------
        application.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(
                    self.admin_handlers.add_admin_start,
                    pattern="^add_admin$"
                )],
                states={
                    ADD_ADMIN: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       self.admin_handlers.add_admin_id)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel)]
            )
        )

        # -------- REPLIES --------
        application.add_handler(
            ConversationHandler(
                entry_points=[CallbackQueryHandler(
                    self.reply_handlers.add_private_reply_start,
                    pattern="^add_private_reply$"
                )],
                states={
                    ADD_PRIVATE_TEXT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       self.reply_handlers.add_private_reply_text)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel)]
            )
        )

        # ==================================================
        # LAST HANDLER (VERY IMPORTANT)
        # ==================================================

        application.add_handler(
            CallbackQueryHandler(self.handle_callback)
        )

    # ==========================================================

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ تم الإلغاء.")
        return ConversationHandler.END
