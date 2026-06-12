from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import ADD_ADMIN, OWNER_ID
from menus import show_admins_menu


# ==================================================
# HELPERS
# ==================================================

def get_cancel_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_admin")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_admins")],
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_admins")],
    ])


def is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


def get_db(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data.get("db")


# ==================================================
# START ADD ADMIN (OWNER ONLY)
# ==================================================

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    user_id = query.from_user.id

    # 🔒 المالك فقط
    if not is_owner(user_id):
        await query.edit_message_text(
            "❌ هذه العملية متاحة للمالك الرئيسي فقط.",
            reply_markup=get_back_keyboard(),
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "👤 أرسل آيدي المستخدم (ID) لإضافته كمشرف:",
        reply_markup=get_cancel_back_keyboard(),
    )

    return ADD_ADMIN


# ==================================================
# RECEIVE ADMIN ID
# ==================================================

async def add_admin_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return ADD_ADMIN

    # 🔒 إعادة التحقق من أن من يرسل ID هو المالك
    user_id = update.effective_user.id if update.effective_user else None

    if not is_owner(user_id):
        await message.reply_text("❌ هذه العملية متاحة للمالك الرئيسي فقط.")
        return ConversationHandler.END

    db = get_db(context)

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        return ConversationHandler.END

    text = message.text.strip()

    if not text.isdigit():
        await message.reply_text("❌ أرسل آيدي رقمي صحيح")
        return ADD_ADMIN

    admin_id = int(text)

    if admin_id <= 0:
        await message.reply_text("❌ آيدي المستخدم غير صحيح")
        return ADD_ADMIN

    try:
        success, _ = db.add_admin(
            admin_id=admin_id,
            username="admin",
            role="مشرف",
            active=True,
        )
    except Exception:
        await message.reply_text("❌ حدث خطأ أثناء إضافة المشرف")
        return ConversationHandler.END

    if success:
        await message.reply_text("✅ تم إضافة المشرف بنجاح")
    else:
        await message.reply_text("❌ فشل إضافة المشرف")

    return ConversationHandler.END


# ==================================================
# CANCEL
# ==================================================

async def cancel_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await show_admins_menu(update, context)
    elif update.message:
        await update.message.reply_text("❌ تم إلغاء إضافة المشرف")

    return ConversationHandler.END


# ==================================================
# BACK
# ==================================================

async def back_to_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await show_admins_menu(update, context)
    elif update.message:
        await update.message.reply_text("🔙 تم الرجوع")

    return ConversationHandler.END


# ==================================================
# CONVERSATION HANDLER
# ==================================================

def get_add_admin_conversation():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_admin_start, pattern="^add_admin$"),
        ],
        states={
            ADD_ADMIN: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_admin_receive,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_admin, pattern="^cancel_add_admin$"),
            CallbackQueryHandler(back_to_admins, pattern="^back_admins$"),
            CommandHandler("cancel", cancel_add_admin),
        ],
        name="add_admin_conversation",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=120,
    )
