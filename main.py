import sys
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from config import BOT_TOKEN, OWNER_ID, MESSAGES
from database.database import BotDatabase
from managers.telegram_manager import TelegramBotManager
from menus import show_main_menu, register_menu_handlers
from conversations.add_account import get_add_account_conversation
from conversations.add_admin import get_add_admin_conversation
from conversations.add_ad import get_add_ad_conversation
from conversations.add_group import get_add_group_conversation
from conversations.add_reply import get_add_reply_conversation
from conversations.set_publish_delay import get_set_publish_delay_conversation
from handlers.account_handlers import AccountHandlers
from handlers.ad_handlers import AdHandlers
from handlers.group_handlers import GroupHandlers
from handlers.reply_handlers import ReplyHandlers
from handlers.admin_handlers import AdminHandlers


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==================================================
# MAIN BOT CLASS
# ==================================================

class MainBot:

    def __init__(self):

        if not BOT_TOKEN:
            print("❌ BOT_TOKEN غير موجود")
            sys.exit(1)

        self.db = BotDatabase()
        self.manager = TelegramBotManager(self.db)

        self.app = Application.builder().token(BOT_TOKEN).build()

        self.app.bot_data["db"] = self.db
        self.app.bot_data["manager"] = self.manager

        self._init_handlers()
        self._register_handlers()

        # إضافة المالك كمشرف إذا لم يكن موجوداً
        if not self.db.is_admin(OWNER_ID):
            self.db.add_admin(
                admin_id=OWNER_ID,
                username="owner",
                role="المالك الرئيسي",
                active=True
            )

    # ==================================================
    # INIT HANDLERS OBJECTS
    # ==================================================

    def _init_handlers(self):

        self.account_handlers = AccountHandlers(self.db)
        self.ad_handlers = AdHandlers(self.db)
        self.group_handlers = GroupHandlers(self.db)
        self.reply_handlers = ReplyHandlers(self.db)
        self.admin_handlers = AdminHandlers(self.db)

        self.app.bot_data["account_handlers"] = self.account_handlers
        self.app.bot_data["ad_handlers"] = self.ad_handlers
        self.app.bot_data["group_handlers"] = self.group_handlers
        self.app.bot_data["reply_handlers"] = self.reply_handlers
        self.app.bot_data["admin_handlers"] = self.admin_handlers

    # ==================================================
    # /start
    # ==================================================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES["unauthorized"])
            return

        await show_main_menu(update, context)

    # ==================================================
    # REGISTER HANDLERS
    # ==================================================

    def _register_handlers(self):

        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start))

        # Publishing control commands (NEW)
        self.app.add_handler(CommandHandler("start_publish", self.manager.start_publish_command))
        self.app.add_handler(CommandHandler("stop_publish", self.manager.stop_publish_command))
        self.app.add_handler(CommandHandler("set_delay", self.manager.set_delay_command))
        
        # Test and info commands
        self.app.add_handler(CommandHandler("testpublish", self.manager.test_publish_once))
        self.app.add_handler(CommandHandler("showgroups", self.manager.show_all_groups))
        self.app.add_handler(CommandHandler("status", self.manager.get_status))

        # Conversations أولاً
        self.app.add_handler(get_add_account_conversation())
        self.app.add_handler(get_add_admin_conversation())
        self.app.add_handler(get_add_ad_conversation())
        self.app.add_handler(get_add_group_conversation())
        self.app.add_handler(get_add_reply_conversation())
        self.app.add_handler(get_set_publish_delay_conversation())

        # Menus أخيراً
        register_menu_handlers(self.app)

        # Error handler
        self.app.add_error_handler(self.error_handler)

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
            except Exception:
                pass

    # ==================================================
    # RUN
    # ==================================================

    def run(self):

        print("🚀 Bot is running...")
        print("📋 الأوامر المتاحة:")
        print("   /start - عرض القائمة الرئيسية")
        print("   /start_publish - بدء النشر التلقائي السريع (في جميع المجموعات وجميع الحسابات)")
        print("   /stop_publish - إيقاف النشر التلقائي")
        print("   /set_delay <ثواني> - تغيير وقت التأخير بين الرسائل (مثال: /set_delay 2)")
        print("   /testpublish - تجربة النشر (أول 3 مجموعات فقط)")
        print("   /showgroups - عرض جميع المجموعات من جميع الحسابات")
        print("   /status - حالة البوت")

        # بدء تشغيل البوت (polling)
        self.app.run_polling()


# ==================================================
# MAIN
# ==================================================

def main():

    bot = MainBot()
    bot.run()


if __name__ == "__main__":
    main()
