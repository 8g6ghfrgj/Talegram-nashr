from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from menus import show_accounts_menu
from config import ADD_ACCOUNT


# ==================================================
# CONSTANTS
# ==================================================

MIN_SESSION_LENGTH = 50

ADD_ACCOUNT_USER_DATA_KEYS = (
    "add_account_session",
)


# ==================================================
# HELPERS
# ==================================================

def clear_add_account_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    يحذف بيانات هذه المحادثة فقط بدون حذف بيانات المستخدم الأخرى.
    """
    for key in ADD_ACCOUNT_USER_DATA_KEYS:
        context.user_data.pop(key, None)


def is_valid_session_format(session: str) -> bool:
    """
    تحقق مبدئي فقط من شكل الجلسة.
    التحقق الحقيقي يجب أن يكون داخل db.add_account أو طبقة Telethon.
    """
    if not session:
        return False

    if len(session) < MIN_SESSION_LENGTH:
        return False

    if any(char.isspace() for char in session):
        return False

    return True


# ==================================================
# START ADD ACCOUNT
# ==================================================

async def add_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    clear_add_account_data(context)

    keyboard = [
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_account")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_accounts")],
    ]

    await query.edit_message_text(
        "📥 أرسل جلسة Telethon (StringSession):",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADD_ACCOUNT


# ==================================================
# RECEIVE SESSION
# ==================================================

async def add_account_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return ADD_ACCOUNT

    session = message.text.strip()
    user_id = update.effective_user.id if update.effective_user else None

    if user_id is None:
        await message.reply_text("❌ تعذر تحديد المستخدم")
        return ConversationHandler.END

    if not is_valid_session_format(session):
        await message.reply_text("❌ الجلسة غير صالحة")
        return ADD_ACCOUNT

    db = context.application.bot_data.get("db")

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        clear_add_account_data(context)
        return ConversationHandler.END

    try:
        success, msg = db.add_account(user_id, session)
    except Exception:
        await message.reply_text("❌ حدث خطأ أثناء إضافة الحساب")
        clear_add_account_data(context)
        return ConversationHandler.END

    if success:
        await message.reply_text("✅ تم إضافة الحساب بنجاح")
    else:
        await message.reply_text(f"❌ فشل الإضافة: {msg}")

    clear_add_account_data(context)
    return ConversationHandler.END


# ==================================================
# CANCEL
# ==================================================

async def cancel_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_add_account_data(context)

    if update.callback_query:
        await update.callback_query.answer()
        await show_accounts_menu(update, context)
    elif update.message:
        await update.message.reply_text("❌ تم إلغاء إضافة الحساب")

    return ConversationHandler.END


# ==================================================
# BACK
# ==================================================

async def back_to_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_add_account_data(context)

    if update.callback_query:
        await update.callback_query.answer()
        await show_accounts_menu(update, context)
    elif update.message:
        await update.message.reply_text("🔙 تم الرجوع")

    return ConversationHandler.END


# ==================================================
# CONVERSATION HANDLER
# ==================================================

def get_add_account_conversation():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_account_start, pattern="^add_account$"),
        ],
        states={
            ADD_ACCOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_account_receive,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_account, pattern="^cancel_add_account$"),
            CallbackQueryHandler(back_to_accounts, pattern="^back_accounts$"),
            CommandHandler("cancel", cancel_add_account),
        ],
        name="add_account_conversation",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=120,
    )
