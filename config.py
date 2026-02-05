import os
from logging import INFO


# ================= BOT =================

BOT_TOKEN = os.environ.get("BOT_TOKEN")


# ================= OWNER =================

OWNER_ID = 8148890042


# ================= DATABASE =================

DB_NAME = "bot_database.db"


# ================= DELAYS =================

DELAY_SETTINGS = {

    "publishing": {
        "between_ads": 0.1,
        "between_groups": 0.2,
        "between_cycles": 30,
        "group_publishing_delay": 60
    },

    "private_reply": {
        "between_replies": 0.05,
        "between_cycles": 3
    },

    "group_reply": {
        "between_replies": 0.05,
        "between_cycles": 3
    },

    "random_reply": {
        "between_replies": 0.05,
        "between_cycles": 3
    },

    "join_groups": {
        "between_links": 90,
        "between_cycles": 5
    }
}


# ================= FILES =================

FILE_SETTINGS = {

    "contact_filename": "تسوي سكليف صحتي واتساب.vcf",

    "directories": {
        "ads": "temp_files/ads",
        "group_replies": "temp_files/group_replies",
        "random_replies": "temp_files/random_replies"
    }
}


# ================= CONVERSATION STATES =================

(
    ADD_ACCOUNT,
    ADD_AD_TYPE,
    ADD_AD_TEXT,
    ADD_AD_MEDIA,
    ADD_GROUP,
    ADD_PRIVATE_REPLY,
    ADD_ADMIN,
    ADD_RANDOM_REPLY,
    ADD_PRIVATE_TEXT,
    ADD_GROUP_TEXT,
    ADD_GROUP_PHOTO
) = range(11)


ADD_GROUP_TEXT_REPLY = 20
ADD_GROUP_PHOTO_REPLY = 21
ADD_GROUP_PHOTO_MEDIA = 22
ADD_RANDOM_MEDIA = 23


# ================= AD TYPES =================

AD_TYPES = {
    "text": "📝 نص فقط",
    "photo": "🖼️ صورة مع نص",
    "contact": "📞 جهة اتصال (VCF)"
}


# ================= GROUP STATUS =================

GROUP_STATUS = {
    "pending": "⏳ معلقة",
    "joined": "✅ منضمة",
    "failed": "❌ فشل"
}


# ================= LOGGING =================

LOGGING_CONFIG = {
    "level": INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "file": "bot.log",
    "max_size": 10 * 1024 * 1024,
    "backup_count": 5
}


# ================= MESSAGES =================

MESSAGES = {

    "start": (
        "🚀 لوحة تحكم البوت\n\n"
        "⚡ نشر سريع مع حماية الحسابات\n"
        "⚡ تأخير 60 ثانية بين القروبات\n"
        "⚡ ردود تلقائية\n"
        "⚡ انضمام سريع\n\n"
        "👑 المالك: 8148890042\n\n"
        "اختر من القائمة:"
    ),

    "unauthorized": "❌ ليس لديك صلاحية.",

    "owner_only": "❌ هذا الأمر للمالك فقط!",

    "no_accounts": "❌ لا توجد حسابات.",

    "no_ads": "❌ لا توجد إعلانات.",

    "no_replies": "❌ لا توجد ردود.",

    "no_groups": "❌ لا توجد مجموعات.",

    "no_admins": "❌ لا يوجد مشرفين."
}


# ================= BUTTONS =================

BUTTONS = {

    "main_menu": {
        "accounts": "👥 الحسابات",
        "ads": "📢 الإعلانات",
        "groups": "👥 المجموعات",
        "replies": "💬 الردود",
        "admins": "👨‍💼 المشرفين",
        "start_publishing": "🚀 بدء النشر",
        "stop_publishing": "⏹️ إيقاف النشر"
    },

    "ad_types": {
        "text": "📝 نصي",
        "photo": "🖼️ صورة",
        "contact": "📞 جهة اتصال"
    },

    "back": "🔙 رجوع",
    "cancel": "❌ إلغاء"
}


# ================= APP LIMITS =================

APP_SETTINGS = {
    "max_accounts_per_admin": 10,
    "max_ads_per_admin": 50,
    "max_groups_per_admin": 100,
    "max_replies_per_admin": 20,
    "session_timeout": 3600,
    "cleanup_interval": 300
}


# ================= DISPLAY =================

DISPLAY_SETTINGS = {
    "truncate_length": 100,
    "ads_per_page": 5,
    "accounts_per_page": 5,
    "groups_per_page": 5,
    "admins_per_page": 5,
    "replies_per_page": 5
}


# ================= FILE TYPES =================

ALLOWED_FILE_TYPES = {
    "photos": [".jpg", ".jpeg", ".png", ".gif"],
    "documents": [".pdf", ".doc", ".docx", ".txt"],
    "contacts": [".vcf"]
}


# ================= CONFIG CHECK =================

def validate_config():

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN غير موجود")
        return False

    if not OWNER_ID:
        print("❌ OWNER_ID غير موجود")
        return False

    return True


def prepare_folders():

    for path in FILE_SETTINGS["directories"].values():
        if not os.path.exists(path):
            os.makedirs(path)


def print_config():

    print("=" * 50)
    print("⚙️ إعدادات البوت")
    print("=" * 50)
    print("👑 المالك:", OWNER_ID)
    print("📊 تأخير القروبات:", DELAY_SETTINGS["publishing"]["group_publishing_delay"])
    print("📁 ملف الاتصال:", FILE_SETTINGS["contact_filename"])
    print("=" * 50)


if __name__ == "__main__":

    print_config()
    prepare_folders()

    if validate_config():
        print("✅ الإعدادات سليمة")
    else:
        print("⚠️ يوجد خطأ في الإعدادات")
