import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters
)

from config import (
    ADD_ACCOUNT,
    ADD_AD_TYPE,
    ADD_AD_TEXT,
    ADD_AD_MEDIA,
    ADD_GROUP,
    ADD_ADMIN,
    ADD_PRIVATE_TEXT,
    ADD_RANDOM_REPLY
)

logger = logging.getLogger(__name__)


class ConversationHandlers:

    def __init__(
        self,
        db,
        manager,
        admin_handlers,
        account_handlers,
        ad_handlers,
        group_handlers,
        reply_handlers
    ):
        self.db = db
        self.manager = manager
        self.admin_handlers = admin_handlers
        self.account_handlers = account_handlers
        self.ad_handlers = ad_handlers
        self.group_handlers = group_handlers
        self.reply_handlers = reply_handlers


    # ==================================================
    # CALLBACK ROUTER
    # ==================================================

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        # ===== Cancel =====
        if data == "cancel_process":
            context.user_data.clear()
            await query.edit_message_text("❌ تم إلغاء العملية")
            return

        # ===== Permission =====
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية")
            return

        # ================= BACK =================

        if data.startswith("back_to_"):
            await self.handle_back(update, context, data)
            return

        # ================= SPEED =================

        if data == "set_publish_delay":
            context.user_data.clear()
            context.user_data["set_delay"] = True

            await query.edit_message_text(
                "⏱ أرسل عدد الثواني بين كل مجموعة:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
                ])
            )
            return

        # ================= ACCOUNTS =================

        if data == "manage_accounts":
            await self.account_handlers.manage_accounts(update, context)

        elif data == "show_accounts":
            await self.account_handlers.show_accounts(update, context)

        elif data == "account_stats":
            await self.account_handlers.show_account_stats(update, context)

        elif data.startswith("delete_account_"):
            await self.account_handlers.delete_account(
                update, context, int(data.split("_")[-1])
            )

        elif data.startswith("toggle_account_"):
            await self.account_handlers.toggle_account_status(
                update, context, int(data.split("_")[-1])
            )

        # ================= ADS =================

        elif data == "manage_ads":
            await self.ad_handlers.manage_ads(update, context)

        elif data == "show_ads":
            await self.ad_handlers.show_ads(update, context)

        elif data == "ad_stats":
            await self.ad_handlers.show_ad_stats(update, context)

        elif data.startswith("delete_ad_"):
            await self.ad_handlers.delete_ad(
                update, context, int(data.split("_")[-1])
            )

        # ================= GROUPS =================

        elif data == "manage_groups":
            await self.group_handlers.manage_groups(update, context)

        elif data == "show_groups":
            await self.group_handlers.show_groups(update, context)

        elif data == "group_stats":
            await self.group_handlers.show_group_stats(update, context)

        elif data == "start_join_groups":
            await self.group_handlers.start_join_groups(update, context)

        elif data == "stop_join_groups":
            await self.group_handlers.stop_join_groups(update, context)

        # ================= ADMINS =================

        elif data == "manage_admins":
            await self.admin_handlers.manage_admins(update, context)

        elif data == "show_admins":
            await self.admin_handlers.show_admins(update, context)

        elif data == "system_stats":
            await self.admin_handlers.show_system_stats(update, context)

        elif data.startswith("delete_admin_"):
            await self.admin_handlers.delete_admin(
                update, context, int(data.split("_")[-1])
            )

        elif data.startswith("toggle_admin_"):
            await self.admin_handlers.toggle_admin_status(
                update, context, int(data.split("_")[-1])
            )

        # ================= REPLIES =================

        elif data == "manage_replies":
            await self.reply_handlers.manage_replies(update, context)

        elif data == "show_private_replies":
            await self.reply_handlers.show_private_replies(update, context)

        elif data == "show_random_replies":
            await self.reply_handlers.show_random_replies(update, context)

        elif data.startswith("delete_private_reply_"):
            await self.reply_handlers.delete_private_reply(
                update, context, int(data.split("_")[-1])
            )

        elif data.startswith("delete_random_reply_"):
            await self.reply_handlers.delete_random_reply(
                update, context, int(data.split("_")[-1])
            )

        # ================= PUBLISH =================

        elif data == "start_publishing":

            accounts = [a for a in self.db.get_accounts(user_id) if a[3] == 1]
            ads = self.db.get_ads(user_id)

            if not accounts:
                await query.edit_message_text("❌ لا توجد حسابات نشطة")
                return

            if not ads:
                await query.edit_message_text("❌ لا توجد إعلانات")
                return

            if self.manager.start_publishing(user_id):
                await query.edit_message_text(
                    f"🚀 بدأ النشر\n⏱ المؤقت: {self.manager.publish_delay} ثانية"
                )
            else:
                await query.edit_message_text("⚠️ النشر يعمل بالفعل")

        elif data == "stop_publishing":

            if self.manager.stop_publishing(user_id):
                await query.edit_message_text("⏹️ تم إيقاف النشر")
            else:
                await query.edit_message_text("⚠️ النشر غير نشط")

        else:
            await query.edit_message_text("❌ زر غير معروف")


    # ==================================================
    # BACK
    # ==================================================

    async def handle_back(self, update, context, data):

        query = update.callback_query

        routes = {
            "back_to_main": self.show_main_menu,
            "back_to_accounts": self.account_handlers.manage_accounts,
            "back_to_ads": self.ad_handlers.manage_ads,
            "back_to_groups": self.group_handlers.manage_groups,
            "back_to_admins": self.admin_handlers.manage_admins,
            "back_to_replies": self.reply_handlers.manage_replies,
        }

        func = routes.get(data)

        if func:
            await func(update, context)
        else:
            await query.edit_message_text("❌ رجوع غير صالح")


    # ==================================================
    # MAIN MENU
    # ==================================================

    async def show_main_menu(self, update, context):

        keyboard = [
            [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="manage_ads")],
            [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
            [InlineKeyboardButton("💬 إدارة الردود", callback_data="manage_replies")],
            [InlineKeyboardButton("👨‍💼 إدارة المشرفين", callback_data="manage_admins")],
            [InlineKeyboardButton("⏱ ضبط وقت النشر", callback_data="set_publish_delay")],
            [InlineKeyboardButton("🚀 بدء النشر", callback_data="start_publishing")],
            [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_publishing")]
        ]

        await update.callback_query.edit_message_text(
            "🎛 لوحة التحكم",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # DELAY INPUT
    # ==================================================

    async def set_delay_handler(self, update, context):

        if not context.user_data.get("set_delay"):
            return

        try:
            delay = float(update.message.text)

            if delay < 1:
                await update.message.reply_text("❌ أقل مدة 1 ثانية")
                return

            self.manager.publish_delay = delay
            context.user_data.clear()

            await update.message.reply_text(f"✅ تم ضبط المؤقت إلى {delay} ثانية")

        except:
            await update.message.reply_text("❌ أرسل رقم صحيح")


    # ==================================================
    # SETUP
    # ==================================================

    def setup_conversation_handlers(self, application):

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_delay_handler)
        )

        # ADD ACCOUNT
        application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self.account_handlers.add_account_start, "^add_account$")],
            states={
                ADD_ACCOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   self.account_handlers.add_account_session)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        ))

        # ADD AD
        application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self.ad_handlers.add_ad_start, "^add_ad$")],
            states={
                ADD_AD_TYPE: [
                    CallbackQueryHandler(self.ad_handlers.add_ad_type, "^ad_type_")
                ],
                ADD_AD_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.ad_handlers.add_ad_text)
                ],
                ADD_AD_MEDIA: [
                    MessageHandler(filters.PHOTO | filters.Document.ALL | filters.CONTACT,
                                   self.ad_handlers.add_ad_media)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        ))

        # ADD GROUP
        application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self.group_handlers.add_group_start, "^add_group$")],
            states={
                ADD_GROUP: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.group_handlers.add_group_link)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        ))

        # ADD ADMIN
        application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self.admin_handlers.add_admin_start, "^add_admin$")],
            states={
                ADD_ADMIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handlers.add_admin_id)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        ))

        # PRIVATE REPLY
        application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self.reply_handlers.add_private_reply_start, "^add_private_reply$")],
            states={
                ADD_PRIVATE_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   self.reply_handlers.add_private_reply_text)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        ))

        # RANDOM REPLY
        application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self.reply_handlers.add_random_reply_start, "^add_random_reply$")],
            states={
                ADD_RANDOM_REPLY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   self.reply_handlers.add_random_reply_text),
                    MessageHandler(filters.PHOTO,
                                   self.reply_handlers.add_random_reply_media)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        ))

        # MAIN CALLBACK
        application.add_handler(CallbackQueryHandler(self.handle_callback))


    # ==================================================
    # CANCEL
    # ==================================================

    async def cancel(self, update, context):

        context.user_data.clear()

        if update.message:
            await update.message.reply_text("❌ تم إلغاء العملية")
        elif update.callback_query:
            await update.callback_query.edit_message_text("❌ تم إلغاء العملية")

        return ConversationHandler.END
