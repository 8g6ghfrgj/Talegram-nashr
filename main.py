import os
import sys
import logging
import asyncio
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from config import BOT_TOKEN, OWNER_ID, MESSAGES
from database.database import BotDatabase
from managers.telegram_manager import TelegramBotManager

from handlers.admin_handlers import AdminHandlers
from handlers.account_handlers import AccountHandlers
from handlers.ad_handlers import AdHandlers
from handlers.group_handlers import GroupHandlers
from handlers.reply_handlers import ReplyHandlers
from handlers.conversation_handlers import ConversationHandlers


# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("temp_files/logs/bot.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


# ================= HEALTH SERVER =================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass


def run_health_server():

    port = int(os.environ.get("PORT", 8080))

    server = HTTPServer(("0.0.0.0", port), HealthHandler)

    logger.info(f"🌐 Health server running on {port}")

    server.serve_forever()


# ================= MAIN BOT =================

class MainBot:

    def __init__(self):

        if not BOT_TOKEN:
            print("❌ BOT_TOKEN غير موجود")
            sys.exit(1)

        if not OWNER_ID:
            print("❌ OWNER_ID غير موجود")
            sys.exit(1)

        self.create_folders()

        self.db = BotDatabase()

        self.manager = TelegramBotManager(self.db)

        self.admin_handlers = AdminHandlers(self.db, self.manager)
        self.account_handlers = AccountHandlers(self.db, self.manager)
        self.ad_handlers = AdHandlers(self.db, self.manager)
        self.group_handlers = GroupHandlers(self.db, self.manager)
        self.reply_handlers = ReplyHandlers(self.db, self.manager)

        self.conversation_handlers = ConversationHandlers(
            self.db,
            self.manager,
            self.admin_handlers,
            self.account_handlers,
            self.ad_handlers,
            self.group_handlers,
            self.reply_handlers
        )

        self.application = Application.builder().token(BOT_TOKEN).build()

        self.setup_handlers()

        self.add_owner()

        logger.info("✅ Bot initialized")


    # ================= SETUP =================

    def create_folders(self):

        paths = [
            "temp_files/ads",
            "temp_files/group_replies",
            "temp_files/random_replies",
            "temp_files/logs"
        ]

        for path in paths:
            os.makedirs(path, exist_ok=True)


    def add_owner(self):

        try:
            self.db.add_admin(
                OWNER_ID,
                "@owner",
                "Main Owner",
                True
            )
        except:
            pass


    # ================= COMMANDS =================

    async def start(self, update: Update, context):

        user_id = update.effective_user.id

        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ ليس لديك صلاحية")
            return

        keyboard = [
            [InlineKeyboardButton("👥 الحسابات", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 الإعلانات", callback_data="manage_ads")],
            [InlineKeyboardButton("👥 المجموعات", callback_data="manage_groups")],
            [InlineKeyboardButton("💬 الردود", callback_data="manage_replies")],
            [InlineKeyboardButton("👨‍💼 المشرفين", callback_data="manage_admins")],
            [InlineKeyboardButton("🚀 بدء النشر", callback_data="start_publishing")],
            [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_publishing")]
        ]

        await update.message.reply_text(
            MESSAGES["start"],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


    async def cancel(self, update: Update, context):

        await update.message.reply_text("❌ تم الإلغاء")

        return ConversationHandler.END


    # ================= CALLBACK =================

    async def handle_callback(self, update: Update, context):

        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية")
            return

        data = query.data

        try:

            if data == "manage_accounts":
                await self.account_handlers.manage_accounts(query, context)

            elif data == "manage_ads":
                await self.ad_handlers.manage_ads(query, context)

            elif data == "manage_groups":
                await self.group_handlers.manage_groups(query, context)

            elif data == "manage_replies":
                await self.reply_handlers.manage_replies(query, context)

            elif data == "manage_admins":
                await self.admin_handlers.manage_admins(query, context)

            elif data == "start_publishing":
                await self.conversation_handlers.start_publishing(query, context)

            elif data == "stop_publishing":
                await self.conversation_handlers.stop_publishing(query, context)

            else:
                await self.conversation_handlers.handle_callback(query, context)

        except Exception as e:

            logger.error(f"Callback error: {e}")

            await query.edit_message_text("❌ حدث خطأ")


    # ================= TEXT HANDLER =================

    async def handle_message(self, update: Update, context):

        user_id = update.message.from_user.id

        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ ليس لديك صلاحية")
            return

        await update.message.reply_text("⚠️ استخدم القائمة")


    # ================= HANDLERS =================

    def setup_handlers(self):

        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("cancel", self.cancel))

        self.conversation_handlers.setup_conversation_handlers(self.application)

        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        self.application.add_error_handler(self.error_handler)


    async def error_handler(self, update: Update, context):

        logger.error(context.error)

        if update and update.effective_message:
            try:
                await update.effective_message.reply_text("❌ خطأ في النظام")
            except:
                pass


    # ================= RUN =================

    def run(self):

        print("🚀 Bot running")

        health_thread = threading.Thread(
            target=run_health_server,
            daemon=True
        )

        health_thread.start()

        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )

        except KeyboardInterrupt:

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.run_until_complete(self.manager.cleanup_all())


# ================= ENTRY =================

def main():

    bot = MainBot()

    bot.run()


if __name__ == "__main__":

    main()
