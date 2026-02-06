import sys
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, OWNER_ID, MESSAGES

from database.database import BotDatabase
from managers.telegram_manager import TelegramBotManager

from handlers.account_handlers import AccountHandlers
from handlers.ad_handlers import AdHandlers
from handlers.group_handlers import GroupHandlers
from handlers.reply_handlers import ReplyHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.conversation_handlers import ConversationHandlers


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==================================================
# MAIN BOT
# ==================================================

class MainBot:

    def __init__(self):

        if not BOT_TOKEN:
            print("❌ BOT_TOKEN غير موجود")
            sys.exit(1)

        # Database + Manager
        self.db = BotDatabase()
        self.manager = TelegramBotManager(self.db)

        # Handlers
        self.account_handlers = AccountHandlers(self.db, self.manager)
        self.ad_handlers = AdHandlers(self.db, self.manager)
        self.group_handlers = GroupHandlers(self.db, self.manager)
        self.reply_handlers = ReplyHandlers(self.db, self.manager)
        self.admin_handlers = AdminHandlers(self.db, self.manager)

        self.conversation_handlers = ConversationHandlers(
            self.db,
            self.manager,
            self.admin_handlers,
            self.account_handlers,
            self.ad_handlers,
            self.group_handlers,
            self.reply_handlers
        )

        # Application
        self.app = Application.builder().token(BOT_TOKEN).build()

        self.setup_handlers()

        # إضافة المالك تلقائياً
        self.db.add_admin(
            OWNER_ID,
            "@owner",
            "المالك الرئيسي",
            True
        )

    # ==================================================
    # START
    # ==================================================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES["unauthorized"])
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

        await update.message.reply_text(
            MESSAGES["start"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # CANCEL
    # ==================================================

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if update.message:
            await update.message.reply_text("❌ تم إلغاء العملية")

        elif update.callback_query:
            await update.callback_query.edit_message_text("❌ تم إلغاء العملية")

        return ConversationHandler.END

    # ==================================================
    # SETUP HANDLERS
    # ==================================================

    def setup_handlers(self):

        # Commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("cancel", self.cancel))

        # Conversations (ALL flows)
        self.conversation_handlers.setup_conversation_handlers(self.app)

        # Main callback router (ONLY ONE)
        self.app.add_handler(
            CallbackQueryHandler(self.conversation_handlers.handle_callback)
        )

        # Fallback text (ignored safely)
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.ignore_message)
        )

        self.app.add_error_handler(self.error_handler)

    # ==================================================
    # IGNORE NORMAL TEXT
    # ==================================================

    async def ignore_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return

    # ==================================================
    # ERRORS
    # ==================================================

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):

        logger.exception(context.error)

        if update and getattr(update, "effective_message", None):
            try:
                await update.effective_message.reply_text(
                    "❌ حدث خطأ في النظام"
                )
            except:
                pass

    # ==================================================
    # RUN
    # ==================================================

    def run(self):

        print("🚀 Bot is running...")
        self.app.run_polling()


# ==================================================
# MAIN
# ==================================================

def main():

    bot = MainBot()
    bot.run()


if __name__ == "__main__":
    main()
