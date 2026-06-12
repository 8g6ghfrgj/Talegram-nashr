from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import ADD_GROUP
from menus import show_groups_menu


# ==================================================
# HELPERS
# ==================================================

def get_cancel_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_group")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_groups")],
    ])


def get_db(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data.get("db")


def normalize_group_link(text: str) -> str:
    """
    تنظيف الرابط أو اليوزرنيم بدون تغيير وظيفته الأساسية.
    """
    text = text.strip()

    if text.startswith("https://t.me/"):
        return text

    if text.startswith("t.me/"):
        return f"https://{text}"

    if text.startswith("@"):
        return text

    return text


def is_valid_group_link(text: str) -> bool:
    """
    تحقق بسيط من أن المدخل رابط تيليجرام أو username.
    """
    if not text:
        return False

    if text.startswith("https://t.me/") and len(text) > len("https://t.me/"):
        return True

    if text.startswith("t.me/") and len(text) > len("t.me/"):
        return True

    if text.startswith("@") and len(text) > 1:
        return True

    return False


# ==================================================
# START ADD GROUP
# ==================================================

async def add_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    await query.edit_message_text(
        "👥 أرسل رابط المجموعة أو الـ @username:",
        reply_markup=get_cancel_back_keyboard(),
    )

    return ADD_GROUP


# ==================================================
# RECEIVE GROUP LINK
# ==================================================

async def add_group_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return ADD_GROUP

    user = update.effective_user

    if not user:
        await message.reply_text("❌ تعذر تحديد المستخدم")
        return ConversationHandler.END

    text = message.text.strip()

    if not is_valid_group_link(text):
        await message.reply_text(
            "❌ الرابط غير صحيح\n"
            "أرسل رابط مثل:\n"
            "https://t.me/example\n"
            "أو @example"
        )
        return ADD_GROUP

    group_link = normalize_group_link(text)

    db = get_db(context)

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        return ConversationHandler.END

    try:
        success, msg = db.add_group(user.id, group_link)
    except Exception:
        await message.reply_text("❌ حدث خطأ أثناء إضافة المجموعة")
        return ConversationHandler.END

    if success:
        await message.reply_text("✅ تم إضافة المجموعة بنجاح")
    else:
        await message.reply_text(f"❌ فشل الإضافة: {msg}")

    return ConversationHandler.END


# ==================================================
# CANCEL
# ==================================================

async def cancel_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await show_groups_menu(update, context)
    elif update.message:
        await update.message.reply_text("❌ تم إلغاء إضافة المجموعة")

    return ConversationHandler.END


# ==================================================
# BACK
# ==================================================

async def back_to_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await show_groups_menu(update, context)
    elif update.message:
        await update.message.reply_text("🔙 تم الرجوع")

    return ConversationHandler.END


# ==================================================
# CONVERSATION HANDLER
# ==================================================

def get_add_group_conversation():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_group_start, pattern="^add_group$"),
        ],
        states={
            ADD_GROUP: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_group_receive,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_group, pattern="^cancel_add_group$"),
            CallbackQueryHandler(back_to_groups, pattern="^back_groups$"),
            CommandHandler("cancel", cancel_add_group),
        ],
        name="add_group_conversation",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=120,
    )
