import os
import sys
import logging
import threading
import asyncio
from datetime import datetime
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler

# التحقق من المتطلبات الأساسية أولاً
REQUIRED_PACKAGES = [
    'telethon',
    'telegram',
    'sqlite3',
    'PIL',
    'apscheduler'
]

missing_packages = []
for package in REQUIRED_PACKAGES:
    try:
        if package == 'telegram':
            import telegram
        elif package == 'PIL':
            import PIL
        elif package == 'sqlite3':
            import sqlite3
        elif package == 'apscheduler':
            import apscheduler
        else:
            __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f"❌ Missing required packages: {', '.join(missing_packages)}")
    print("📦 Please install them using: pip install -r requirements.txt")
    sys.exit(1)

print("✅ All required packages are installed")

# الآن استيراد باقي المكتبات
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# استيراد المكونات من الهيكل الجديد
try:
    from config import BOT_TOKEN, OWNER_ID
    from database.database import BotDatabase
    from managers.telegram_manager import TelegramBotManager
    from handlers.admin_handlers import AdminHandlers
    from handlers.account_handlers import AccountHandlers
    from handlers.ad_handlers import AdHandlers
    from handlers.group_handlers import GroupHandlers
    from handlers.reply_handlers import ReplyHandlers
    from handlers.conversation_handlers import ConversationHandlers
    from config import (
        ADD_ACCOUNT, ADD_AD_TYPE, ADD_AD_TEXT, ADD_AD_MEDIA,
        ADD_GROUP, ADD_PRIVATE_REPLY, ADD_ADMIN,
        ADD_RANDOM_REPLY, ADD_PRIVATE_TEXT, ADD_GROUP_TEXT,
        ADD_GROUP_PHOTO, MESSAGES
    )
except ImportError as e:
    print(f"❌ خطأ في استيراد المكونات: {e}")
    print("📁 تأكد من وجود جميع الملفات والمجلدات")
    sys.exit(1)

# إعداد السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('temp_files/logs/bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# خادم HTTP للتحقق من الصحة
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Bot is running!')
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "service": "telegram-auto-bot"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # تقليل الضوضاء في سجلات HTTP
        pass

def run_health_server():
    """تشغيل خادم HTTP للتحقق من الصحة"""
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Health server running on port {port}")
        print(f"🌐 Health check available at: http://0.0.0.0:{port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Failed to start health server: {e}")
        print(f"❌ Health server error: {e}")

class MainBot:
    def __init__(self):
        # التحقق من التوكن
        if not BOT_TOKEN:
            print("❌ خطأ: لم يتم تعيين BOT_TOKEN في متغيرات البيئة")
            print("⚠️ يرجى إضافة BOT_TOKEN في Render.com → Environment")
            print("📝 أو في ملف .env: BOT_TOKEN=your_bot_token_here")
            sys.exit(1)
        
        # التحقق من المالك
        if not OWNER_ID:
            print("❌ خطأ: لم يتم تعيين OWNER_ID في config.py")
            sys.exit(1)
        
        print(f"👑 المالك المحدد: {OWNER_ID}")
        
        # إنشاء المجلدات المطلوبة
        self._create_directories()
        
        # تهيئة قاعدة البيانات
        print("📊 جاري تهيئة قاعدة البيانات...")
        try:
            self.db = BotDatabase()
            print("✅ تم تهيئة قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في قاعدة البيانات: {e}")
            sys.exit(1)
        
        # تهيئة المدير
        print("🚀 جاري تهيئة مدير تليجرام...")
        try:
            self.manager = TelegramBotManager(self.db)
            print("✅ تم تهيئة مدير تليجرام")
        except Exception as e:
            print(f"❌ خطأ في مدير تليجرام: {e}")
            sys.exit(1)
        
        # تهيئة المعالجات
        print("⚙️ جاري تهيئة المعالجات...")
        try:
            self.admin_handlers = AdminHandlers(self.db, self.manager)
            self.account_handlers = AccountHandlers(self.db, self.manager)
            self.ad_handlers = AdHandlers(self.db, self.manager)
            self.group_handlers = GroupHandlers(self.db, self.manager)
            self.reply_handlers = ReplyHandlers(self.db, self.manager)
            self.conversation_handlers = ConversationHandlers(
                self.db, self.manager, self.admin_handlers,
                self.account_handlers, self.ad_handlers,
                self.group_handlers, self.reply_handlers
            )
            print("✅ تم تهيئة جميع المعالجات")
        except Exception as e:
            print(f"❌ خطأ في المعالجات: {e}")
            sys.exit(1)
        
        # تهيئة التطبيق
        print("🤖 جاري تهيئة تطبيق تليجرام...")
        try:
            self.application = Application.builder().token(BOT_TOKEN).build()
            print("✅ تم تهيئة تطبيق تليجرام")
        except Exception as e:
            print(f"❌ خطأ في تطبيق تليجرام: {e}")
            sys.exit(1)
        
        # إعداد المعالجات
        self.setup_handlers()
        
        # إضافة المالك الرئيسي إذا لم يكن موجوداً
        self._add_owner()
        
        # متغير لحفظ سياق المستخدمين
        self.user_conversations = {}
        
        print("🎉 تم تهيئة البوت بنجاح!")
    
    def _create_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = [
            "temp_files/ads",
            "temp_files/group_replies", 
            "temp_files/random_replies",
            "temp_files/logs",
            "temp_files/backups",
            "temp_files/exports",
            "database"
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"✅ تم إنشاء المجلد: {directory}")
            except Exception as e:
                print(f"⚠️ خطأ في إنشاء {directory}: {e}")
    
    def _add_owner(self):
        """إضافة المالك الرئيسي إلى قاعدة البيانات"""
        try:
            success, message = self.db.add_admin(OWNER_ID, "@owner", "المالك الرئيسي", True)
            if success:
                logger.info(f"✅ {message}")
                print(f"✅ {message}")
            else:
                logger.info(f"⚠️ {message}")
                print(f"⚠️ {message}")
        except Exception as e:
            logger.error(f"خطأ في إضافة المالك: {e}")
            print(f"⚠️ خطأ في إضافة المالك: {e}")
    
    def get_user_context(self, user_id):
        """الحصول على سياق المستخدم"""
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = {}
        return self.user_conversations[user_id]
    
    async def start(self, update: Update, context):
        """بدء البوت"""
        user = update.effective_user
        user_id = user.id
        
        # تسجيل وصول المستخدم
        logger.info(f"👤 المستخدم {user_id} ({user.username}) أرسل /start")
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(
                "❌ ليس لديك صلاحية للوصول إلى هذا البوت.\n\n"
                "👑 فقط المشرفين المصرح لهم يمكنهم استخدام البوت."
            )
            return
        
        user_context = self.get_user_context(user_id)
        user_context['conversation_active'] = False
        
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
        
        welcome_text = (
            "🚀 **لوحة تحكم البوت الفعلي - الإصدار المعدل**\n\n"
            "⚡ **المميزات:**\n"
            "• النشر بأقصى سرعة مع تأمين الحسابات\n"
            "• تأخير 60 ثانية بين نشر القروبات\n"
            "• الردود التلقائية بأقصى سرعة\n"
            "• الانضمام للمجموعات تلقائياً\n\n"
            "👑 **المالك الوحيد:** `{owner_id}`\n\n"
            "📊 **إحصائيات سريعة:**\n"
            "• الحسابات: {accounts_count}\n"
            "• الإعلانات: {ads_count}\n"
            "• المجموعات: {groups_count}\n\n"
            "اختر الإجراء الذي تريد تنفيذه:"
        ).format(
            owner_id=OWNER_ID,
            accounts_count=len(self.db.get_accounts()),
            ads_count=len(self.db.get_ads()),
            groups_count=len(self.db.get_groups())
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def cancel(self, update: Update, context):
        """إلغاء الأمر الحالي"""
        user_id = update.message.from_user.id
        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ ليس لديك صلاحية للوصول إلى هذا البوت.")
            return
        
        user_context = self.get_user_context(user_id)
        user_context['conversation_active'] = False
        
        await update.message.reply_text("❌ تم إلغاء الأمر.")
        await self.start(update, context)
        return ConversationHandler.END
    
    async def handle_callback(self, update: Update, context):
        """معالجة الأزرار"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # تسجيل النقر
        logger.info(f"🖱️ المستخدم {user_id} نقر على: {query.data}")
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية للوصول إلى هذا البوت.")
            return
        
        data = query.data
        
        # توجيه الأزرار إلى المعالجات المناسبة
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
            elif data in ["back_to_main", "back_to_accounts", "back_to_ads", 
                         "back_to_groups", "back_to_replies", "back_to_admins",
                         "back_to_private_replies", "back_to_group_replies"]:
                await self.conversation_handlers.handle_back_buttons(query, context, data)
            else:
                # معالجة الأزرار الأخرى عبر conversation_handlers
                await self.conversation_handlers.handle_callback(query, context)
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الزر {data}: {e}")
            await query.edit_message_text(
                f"❌ حدث خطأ في معالجة الأمر:\n\n`{str(e)[:100]}...`\n\n"
                "يرجى المحاولة مرة أخرى أو الاتصال بالمطور."
            )
    
    async def handle_message(self, update: Update, context):
        """معالجة الرسائل النصية العامة"""
        user_id = update.message.from_user.id
        message_text = update.message.text
        
        # تسجيل الرسالة
        logger.info(f"💬 المستخدم {user_id} أرسل: {message_text[:50]}...")
        
        # إذا لم يكن المستخدم مشرفاً
        if not self.db.is_admin(user_id):
            await update.message.reply_text(
                "❌ ليس لديك صلاحية للوصول إلى هذا البوت.\n\n"
                "استخدم /start للبدء إذا كنت مشرفاً."
            )
            return
        
        # إذا كان الأمر خارج المحادثة النشطة
        user_context = self.get_user_context(user_id)
        if not user_context.get('conversation_active', False):
            await update.message.reply_text(
                "⚠️ لا توجد محادثة نشطة.\n\n"
                "استخدم /start للعودة إلى القائمة الرئيسية."
            )
    
    async def stats_command(self, update: Update, context):
        """أمر لعرض إحصائيات النظام"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ ليس لديك صلاحية.")
            return
        
        stats = self.db.get_statistics()
        manager_stats = self.manager.get_stats()
        
        text = (
            "📊 **إحصائيات النظام**\n\n"
            "👥 **الحسابات:**\n"
            f"• الإجمالي: {stats['accounts']['total']}\n"
            f"• النشطة: {stats['accounts']['active']}\n\n"
            
            "📢 **الإعلانات:** {ads_count}\n\n"
            
            "👥 **المجموعات:**\n"
            f"• الإجمالي: {stats['groups']['total']}\n"
            f"• المنضمة: {stats['groups']['joined']}\n\n"
            
            "⚡ **المهام النشطة:**\n"
            f"• النشر: {'✅' if manager_stats['active_tasks']['publishing'] else '❌'}\n"
            f"• الرد الخاص: {'✅' if manager_stats['active_tasks']['private_reply'] else '❌'}\n"
            f"• الرد الجماعي: {'✅' if manager_stats['active_tasks']['group_reply'] else '❌'}\n"
            f"• الرد العشوائي: {'✅' if manager_stats['active_tasks']['random_reply'] else '❌'}\n"
            f"• الانضمام: {'✅' if manager_stats['active_tasks']['join_groups'] else '❌'}\n\n"
            
            "📈 **الإنجازات:**\n"
            f"• نشر: {manager_stats['publish_count']}\n"
            f"• ردود: {manager_stats['reply_count']}\n"
            f"• انضمام: {manager_stats['join_count']}\n"
            f"• أخطاء: {manager_stats['errors']}\n\n"
            
            "🔄 **آخر تحديث:** {time}"
        ).format(
            ads_count=stats['ads'],
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context):
        """أمر المساعدة"""
        help_text = (
            "🆘 **دليل استخدام البوت**\n\n"
            
            "📋 **الأوامر الأساسية:**\n"
            "• /start - عرض القائمة الرئيسية\n"
            "• /stats - عرض إحصائيات النظام\n"
            "• /help - عرض هذه الرسالة\n"
            "• /cancel - إلغاء الأمر الحالي\n\n"
            
            "⚡ **الميزات الرئيسية:**\n"
            "1. **إدارة الحسابات** - إضافة/حذف حسابات تليجرام\n"
            "2. **إدارة الإعلانات** - نشر نصوص، صور، جهات اتصال\n"
            "3. **إدارة المجموعات** - انضمام تلقائي للمجموعات\n"
            "4. **الردود التلقائية** - في الخاص والمجموعات\n"
            "5. **نظام المشرفين** - إدارة صلاحيات المستخدمين\n\n"
            
            "⚠️ **ملاحظات مهمة:**\n"
            "• تأخير 60 ثانية بين نشر القروبات\n"
            "• فقط المالك يمكنه إضافة مشرفين\n"
            "• استخدم الأزرار للتنقل بين القوائم\n\n"
            
            "👑 **المالك:** `{owner_id}`\n"
            "📞 **للإبلاغ عن مشاكل:** راسل المالك"
        ).format(owner_id=OWNER_ID)
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def debug_command(self, update: Update, context):
        """أمر تصحيح للأخطاء (للمالك فقط)"""
        user_id = update.message.from_user.id
        
        if user_id != OWNER_ID:
            await update.message.reply_text("❌ هذا الأمر للمالك فقط.")
            return
        
        import platform
        import psutil
        import json
        
        # جمع معلومات النظام
        system_info = {
            "python_version": platform.python_version(),
            "system": platform.system(),
            "release": platform.release(),
            "bot_token_set": bool(BOT_TOKEN),
            "owner_id": OWNER_ID,
            "current_time": datetime.now().isoformat(),
            "memory_usage": psutil.virtual_memory().percent,
            "cpu_usage": psutil.cpu_percent(interval=1)
        }
        
        # معلومات قاعدة البيانات
        try:
            db_stats = self.db.get_statistics()
            system_info["database"] = db_stats
        except Exception as e:
            system_info["database_error"] = str(e)
        
        # معلومات المدير
        try:
            manager_stats = self.manager.get_stats()
            system_info["manager"] = manager_stats
        except Exception as e:
            system_info["manager_error"] = str(e)
        
        # عرض المعلومات
        debug_text = (
            "🐛 **معلومات التصحيح**\n\n"
            "```json\n{info}\n```\n\n"
            "📁 **المجلدات:**\n"
            "• temp_files/ads: {ads_count} ملف\n"
            "• temp_files/group_replies: {group_replies_count} ملف\n"
            "• temp_files/random_replies: {random_replies_count} ملف"
        ).format(
            info=json.dumps(system_info, indent=2, ensure_ascii=False),
            ads_count=len(os.listdir("temp_files/ads")) if os.path.exists("temp_files/ads") else 0,
            group_replies_count=len(os.listdir("temp_files/group_replies")) if os.path.exists("temp_files/group_replies") else 0,
            random_replies_count=len(os.listdir("temp_files/random_replies")) if os.path.exists("temp_files/random_replies") else 0
        )
        
        await update.message.reply_text(debug_text, parse_mode='Markdown')
    
    def setup_handlers(self):
        """إعداد معالجات البوت"""
        # معالجات الأوامر الأساسية
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("cancel", self.cancel))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))
        
        # إضافة معالجات المحادثة
        self.conversation_handlers.setup_conversation_handlers(self.application)
        
        # معالج الأزرار
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # معالج الرسائل العامة (للرد على الأوامر في المحادثات)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # معالج الأخطاء
        self.application.add_error_handler(self.error_handler)
        
        logger.info("✅ تم إعداد جميع المعالجات")
        print("✅ تم إعداد جميع المعالجات")
    
    async def error_handler(self, update: Update, context):
        """معالج الأخطاء العام"""
        logger.error(f"❌ حدث خطأ: {context.error}")
        
        # إذا كان هناك تحديث، أرسل رسالة للمستخدم
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ حدث خطأ غير متوقع في النظام.\n\n"
                    "الرجاء المحاولة مرة أخرى أو الاتصال بالمطور."
                )
            except:
                pass
        
        # تسجيل تفاصيل الخطأ
        try:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"تفاصيل الخطأ:\n{error_details}")
            
            # حفظ الخطأ في ملف
            with open("temp_files/logs/errors.log", "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now()}] {context.error}\n{error_details}\n")
        except:
            pass
    
    def run(self):
        """تشغيل البوت"""
        print("=" * 60)
        print("🚀 بوت النشر الفعلي - الإصدار المعدل")
        print("=" * 60)
        print(f"👑 المالك: {OWNER_ID}")
        print("⚡ الميزات:")
        print("   • تأخير نشر القروبات: 60 ثانية")
        print("   • النشر بأقصى سرعة")
        print("   • نظام صلاحيات متقدم")
        print("   • تشفير متقدم للنصوص")
        print("=" * 60)
        print("📊 البوت يعمل الآن! اضغط Ctrl+C للإيقاف")
        print("=" * 60)
        
        # بدء خادم HTTP في خيط منفصل
        http_thread = threading.Thread(target=run_health_server, daemon=True)
        http_thread.start()
        print("🌐 خادم الصحة يعمل على المنفذ 8080")
        
        # تشغيل البوت
        try:
            print("🤖 جاري تشغيل البوت...")
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
        except KeyboardInterrupt:
            print("\n\n🛑 إيقاف البوت...")
            # تنظيف الموارد
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.manager.cleanup_all())
            print("✅ تم تنظيف الموارد")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
            print(f"❌ خطأ في تشغيل البوت: {e}")
            raise

def main():
    """الدالة الرئيسية"""
    try:
        # عرض معلومات البدء
        print("🎬 بدء تشغيل البوت الفعلي...")
        print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 إصدار Python: {sys.version}")
        
        # تشغيل البوت
        bot = MainBot()
        bot.run()
        
    except Exception as e:
        print(f"💥 خطأ فادح في تشغيل البوت: {e}")
        import traceback
        traceback.print_exc()
        
        # محاولة إعادة التشغيل بعد 5 ثواني
        print("🔄 جاري إعادة التشغيل بعد 5 ثواني...")
        import time
        time.sleep(5)
        
        # إعادة التشغيل
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    main()
