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
        [InlineKeyboardButton("🚀 بدء النشر", callback_data="start_publishing")],
        [InlineKeyboardButton("⏹ إيقاف النشر", callback_data="stop_publishing")]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎛 لوحة التحكم الرئيسية",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "🎛 لوحة التحكم الرئيسية",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ==================================================
# ACCOUNTS MENU
# ==================================================

async def show_accounts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")],
        [InlineKeyboardButton("📋 عرض الحسابات", callback_data="show_accounts")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]

    await update.callback_query.edit_message_text(
        "👥 إدارة الحسابات",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# ADS MENU
# ==================================================

async def show_ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("➕ إضافة إعلان", callback_data="add_ad")],
        [InlineKeyboardButton("📋 عرض الإعلانات", callback_data="show_ads")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="ad_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]

    await update.callback_query.edit_message_text(
        "📢 إدارة الإعلانات",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# GROUPS MENU
# ==================================================

async def show_groups_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("➕ إضافة مجموعة", callback_data="add_group")],
        [InlineKeyboardButton("📋 عرض المجموعات", callback_data="show_groups")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="group_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]

    await update.callback_query.edit_message_text(
        "👥 إدارة المجموعات",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# REPLIES MENU
# ==================================================

async def show_replies_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("➕ إضافة رد خاص", callback_data="add_private_reply")],
        [InlineKeyboardButton("➕ إضافة رد عشوائي", callback_data="add_random_reply")],
        [InlineKeyboardButton("📋 عرض الردود", callback_data="show_replies")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]

    await update.callback_query.edit_message_text(
        "💬 إدارة الردود",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# ADMINS MENU
# ==================================================

async def show_admins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")],
        [InlineKeyboardButton("📋 عرض المشرفين", callback_data="show_admins")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]

    await update.callback_query.edit_message_text(
        "👨‍💼 إدارة المشرفين",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# CALLBACK ROUTER (ONE ONLY)
# ==================================================

async def menus_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # fetch handlers
    account_handlers = context.application.bot_data.get("account_handlers")
    ad_handlers = context.application.bot_data.get("ad_handlers")
    group_handlers = context.application.bot_data.get("group_handlers")
    reply_handlers = context.application.bot_data.get("reply_handlers")
    admin_handlers = context.application.bot_data.get("admin_handlers")
    manager = context.application.bot_data.get("manager")

    # ---------- BACK ----------
    if data == "back_main":
        await show_main_menu(update, context)

    elif data == "back_accounts":
        await show_accounts_menu(update, context)

    elif data == "back_ads":
        await show_ads_menu(update, context)

    elif data == "back_groups":
        await show_groups_menu(update, context)

    elif data == "back_replies":
        await show_replies_menu(update, context)

    elif data == "back_admins":
        await show_admins_menu(update, context)

    # ---------- MENUS ----------
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

    # ---------- CONVERSATIONS ----------
    elif data == "add_account":
        await query.edit_message_text("⚠️ هذه الخاصية تحتاج إلى تفعيل - سيتم إضافتها قريباً")

    elif data == "add_ad":
        await query.edit_message_text("⚠️ هذه الخاصية تحتاج إلى تفعيل - سيتم إضافتها قريباً")

    elif data == "add_group":
        await query.edit_message_text("⚠️ هذه الخاصية تحتاج إلى تفعيل - سيتم إضافتها قريباً")

    elif data == "add_admin":
        await query.edit_message_text("⚠️ هذه الخاصية تحتاج إلى تفعيل - سيتم إضافتها قريباً")

    elif data == "add_private_reply":
        await query.edit_message_text("⚠️ هذه الخاصية تحتاج إلى تفعيل - سيتم إضافتها قريباً")

    elif data == "add_random_reply":
        await query.edit_message_text("⚠️ هذه الخاصية تحتاج إلى تفعيل - سيتم إضافتها قريباً")

    elif data == "menu_set_delay":
        await query.edit_message_text("⚠️ هذه الخاصية تحتاج إلى تفعيل - سيتم إضافتها قريباً")

    # ---------- ACCOUNTS ----------
    elif data == "show_accounts":
        if account_handlers:
            await account_handlers.show_accounts(update, context)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الحسابات غير متاح حالياً")

    elif data.startswith("toggle_account_"):
        if account_handlers:
            acc_id = int(data.split("_")[-1])
            await account_handlers.toggle_account(update, context, acc_id)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الحسابات غير متاح حالياً")

    elif data.startswith("delete_account_"):
        if account_handlers:
            acc_id = int(data.split("_")[-1])
            await account_handlers.delete_account(update, context, acc_id)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الحسابات غير متاح حالياً")

    # ---------- ADS ----------
    elif data == "show_ads":
        if ad_handlers:
            await ad_handlers.show_ads(update, context)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الإعلانات غير متاح حالياً")

    elif data == "ad_stats":
        if ad_handlers:
            await ad_handlers.ad_stats(update, context)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الإعلانات غير متاح حالياً")

    elif data.startswith("delete_ad_"):
        if ad_handlers:
            ad_id = int(data.split("_")[-1])
            await ad_handlers.delete_ad(update, context, ad_id)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الإعلانات غير متاح حالياً")

    # ---------- GROUPS ----------
    elif data == "show_groups":
        if group_handlers:
            await group_handlers.show_groups(update, context)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام المجموعات غير متاح حالياً")

    elif data == "group_stats":
        if group_handlers:
            await group_handlers.group_stats(update, context)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام المجموعات غير متاح حالياً")

    elif data.startswith("delete_group_"):
        if group_handlers:
            group_id = int(data.split("_")[-1])
            await group_handlers.delete_group(update, context, group_id)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام المجموعات غير متاح حالياً")

    # ---------- REPLIES ----------
    elif data == "show_replies":
        if reply_handlers:
            await reply_handlers.show_replies(update, context)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الردود غير متاح حالياً")

    elif data.startswith("delete_private_reply_"):
        if reply_handlers:
            rid = int(data.split("_")[-1])
            await reply_handlers.delete_private_reply(update, context, rid)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الردود غير متاح حالياً")

    elif data.startswith("delete_random_reply_"):
        if reply_handlers:
            rid = int(data.split("_")[-1])
            await reply_handlers.delete_random_reply(update, context, rid)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام الردود غير متاح حالياً")

    # ---------- ADMINS ----------
    elif data == "show_admins":
        if admin_handlers:
            await admin_handlers.show_admins(update, context)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام المشرفين غير متاح حالياً")

    elif data.startswith("delete_admin_"):
        if admin_handlers:
            aid = int(data.split("_")[-1])
            await admin_handlers.delete_admin(update, context, aid)
        else:
            await query.edit_message_text("⚠️ عذراً، نظام المشرفين غير متاح حالياً")

    # ---------- PUBLISH ----------
    elif data == "start_publishing":
        if manager:
            if manager.start_publishing(query.from_user.id):
                await query.edit_message_text("🚀 تم بدء النشر")
            else:
                await query.edit_message_text("⚠️ النشر يعمل بالفعل")
        else:
            await query.edit_message_text("⚠️ عذراً، نظام النشر غير متاح حالياً")

    elif data == "stop_publishing":
        if manager:
            if manager.stop_publishing(query.from_user.id):
                await query.edit_message_text("⏹ تم إيقاف النشر")
            else:
                await query.edit_message_text("⚠️ النشر غير نشط")
        else:
            await query.edit_message_text("⚠️ عذراً، نظام النشر غير متاح حالياً")

    else:
        await query.edit_message_text("❌ زر غير معروف")


# ==================================================
# REGISTER HANDLER
# ==================================================

def register_menu_handlers(application):

    application.add_handler(
        CallbackQueryHandler(menus_callback_router)
    )
