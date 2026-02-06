import sys
import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# ================= PATH FIX (Render Safe) =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# ================= CONFIG =================

from config import BOT_TOKEN, OWNER_ID, MESSAGES

# ================= CORE =================

from database.database import BotDatabase
from managers.telegram_manager import TelegramBotManager

# ================= HANDLERS =================

from handlers.account_handlers import AccountHandlers
from handlers.ad_handlers import AdHandlers
from handlers.group_handlers import GroupHandlers
from handlers.reply_handlers import ReplyHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.conversation_handlers import ConversationHandlers


# ================= LOGGING =================

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

        # ===== Database =====
        self.db = BotDatabase()

        # ===== Manager =====
        self.manager = TelegramBotManager(self.db)

        # ===== Handlers =====
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

        # ===== Telegram Application =====
        self.app = Application.builder().token(BOT_TOKEN).build()

        self.setup_handlers()

        # ===== Add owner as admin automatically =====
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

        context.user_data.clear()

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

        # All conversations & callbacks
        self.conversation_handlers.setup_conversation_handlers(self.app)

        # Ignore random messages outside flows
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.ignore_message)
        )

        # Errors
        self.app.add_error_handler(self.error_handler)


    # ==================================================
    # IGNORE TEXT
    # ==================================================

    async def ignore_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return


    # ==================================================
    # ERROR HANDLER
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
        self.app.run_polling(drop_pending_updates=True)



# ==================================================
# MAIN
# ==================================================

def main():
    bot = MainBot()
    bot.run()


if __name__ == "__main__":
    main()
