from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler


# ==================================================
# MAIN MENU
# ==================================================

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="menu_accounts")],
        [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="menu_ads")],
        [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="menu_groups")],
        [InlineKeyboardButton("💬 إدارة الردود", callback_data="menu_replies")],
        [InlineKeyboardButton("👨‍💼 إدارة المشرفين", callback_data="menu_admins")],
        [InlineKeyboardButton("⏱ ضبط وقت النشر", callback_data="menu_set_delay")],
        [InlineKeyboardButton("🚀 بدء النشر", callback_data="menu_start_publish")],
        [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="menu_stop_publish")]
    ]

    if update.message:
        await update.message.reply_text(
            "🎛 لوحة التحكم الرئيسية",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.callback_query.edit_message_text(
            "🎛 لوحة التحكم الرئيسية",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ==================================================
# SUB MENUS
# ==================================================

async def show_accounts_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")],
        [InlineKeyboardButton("📋 عرض الحسابات", callback_data="show_accounts")],
        [InlineKeyboardButton("📊 إحصائيات الحسابات", callback_data="account_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]
    await update.callback_query.edit_message_text(
        "👥 إدارة الحسابات",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_ads_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة إعلان", callback_data="add_ad")],
        [InlineKeyboardButton("📋 عرض الإعلانات", callback_data="show_ads")],
        [InlineKeyboardButton("📊 إحصائيات الإعلانات", callback_data="ad_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]
    await update.callback_query.edit_message_text(
        "📢 إدارة الإعلانات",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_groups_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مجموعة", callback_data="add_group")],
        [InlineKeyboardButton("📋 عرض المجموعات", callback_data="show_groups")],
        [InlineKeyboardButton("📊 إحصائيات المجموعات", callback_data="group_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]
    await update.callback_query.edit_message_text(
        "👥 إدارة المجموعات",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_replies_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("➕ رد خاص", callback_data="add_private_reply")],
        [InlineKeyboardButton("➕ رد عشوائي", callback_data="add_random_reply")],
        [InlineKeyboardButton("📋 عرض الردود", callback_data="show_replies")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]
    await update.callback_query.edit_message_text(
        "💬 إدارة الردود",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_admins_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")],
        [InlineKeyboardButton("📋 عرض المشرفين", callback_data="show_admins")],
        [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="system_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]
    await update.callback_query.edit_message_text(
        "👨‍💼 إدارة المشرفين",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# CALLBACK ROUTER (MENUS ONLY)
# ==================================================

async def menus_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_main":
        await show_main_menu(update, context)

    elif data == "menu_accounts":
        await show_accounts_menu(update, context)

    elif data == "menu_ads":
        await show_ads_menu(update, context)

    elif data == "menu_groups":
        await show_groups_menu(update, context)

    elif data == "menu_replies":
        await show_replies_menu(update, context)

    elif data == "menu_admins":
        await show_admins_menu(update, context)

    # هذه الأزرار ستُربط لاحقًا بالـ Conversations / Manager
    elif data == "menu_set_delay":
        await query.edit_message_text(
            "⏱ سيتم ضبط وقت النشر من المحادثة التالية.\n(قيد الربط)"
        )

    elif data == "menu_start_publish":
        await query.edit_message_text(
            "🚀 بدء النشر سيتم ربطه بالمدير.\n(قيد الربط)"
        )

    elif data == "menu_stop_publish":
        await query.edit_message_text(
            "⏹️ إيقاف النشر سيتم ربطه بالمدير.\n(قيد الربط)"
        )


# ==================================================
# REGISTER MENU HANDLERS
# ==================================================

def register_menu_handlers(application):

    application.add_handler(
        CallbackQueryHandler(menus_callback_router)
    )
