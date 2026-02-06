import os
from logging import INFO


# ==================================================
# BOT
# ==================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ==================================================
# OWNER
# ==================================================

OWNER_ID = 8148890042


# ==================================================
# DATABASE
# ==================================================

DB_NAME = "bot_database.db"


# ==================================================
# DELAYS
# ==================================================

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


# ==================================================
# FILES
# ==================================================

FILE_SETTINGS = {

    "directories": {
        "ads": "temp_files/ads",
        "group_replies": "temp_files/group_replies",
        "random_replies": "temp_files/random_replies"
    }
}


# ==================================================
# CONVERSATION STATES
# ==================================================

(
    ADD_ACCOUNT,
    ADD_AD_TYPE,
    ADD_AD_TEXT,
    ADD_AD_MEDIA,
    ADD_GROUP,
    ADD_ADMIN,
    ADD_PRIVATE_TEXT,
    ADD_RANDOM_REPLY
) = range(8)


# ==================================================
# AD TYPES
# ==================================================

AD_TYPES = {
    "text": "📝 نص فقط",
    "photo": "🖼️ صورة مع نص",
    "contact": "📞 جهة اتصال (VCF)"
}


# ==================================================
# GROUP STATUS
# ==================================================

GROUP_STATUS = {
    "pending": "⏳ معلقة",
    "joined": "✅ منضمة",
    "failed": "❌ فشل"
}


# ==================================================
# LOGGING
# ==================================================

LOGGING_CONFIG = {
    "level": INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "file": "bot.log",
}


# ==================================================
# MESSAGES
# ==================================================

MESSAGES = {

    "start": (
        "🚀 لوحة تحكم البوت\n\n"
        "⚡ نشر تلقائي\n"
        "⚡ ردود ذكية\n"
        "⚡ انضمام للمجموعات\n\n"
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


# ==================================================
# LIMITS
# ==================================================

APP_SETTINGS = {
    "max_accounts_per_admin": 10,
    "max_ads_per_admin": 50,
    "max_groups_per_admin": 100,
    "max_replies_per_admin": 20
}


# ==================================================
# HELPERS
# ==================================================

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
        os.makedirs(path, exist_ok=True)


if __name__ == "__main__":

    prepare_folders()

    if validate_config():
        print("✅ الإعدادات سليمة")
    else:
        print("⚠️ يوجد خطأ في الإعدادات")
