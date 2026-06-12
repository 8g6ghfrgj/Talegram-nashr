from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from menus import show_main_menu


SET_DELAY = 100  # حالة محادثة مستقلة


# ==================================================
# HELPERS
# ==================================================

def get_cancel_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_set_delay")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ])


def get_manager(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data.get("manager")


# ==================================================
# START
# ==================================================

async def set_delay_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    await query.edit_message_text(
        "⏱ أرسل عدد الثواني بين كل مجموعة (مثال: 5):",
        reply_markup=get_cancel_back_keyboard(),
    )

    return SET_DELAY


# ==================================================
# RECEIVE DELAY
# ==================================================

async def set_delay_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return SET_DELAY

    manager = get_manager(context)

    if manager is None:
        await message.reply_text("❌ خطأ داخلي: مدير النشر غير مهيأ")
        return ConversationHandler.END

    text = message.text.strip()

    try:
        delay = float(text)
    except ValueError:
        await message.reply_text("❌ أرسل رقم صحيح")
        return SET_DELAY

    if delay < 1:
        await message.reply_text("❌ أقل مدة هي 1 ثانية")
        return SET_DELAY

    try:
        manager.publish_delay = delay
    except Exception:
        await message.reply_text("❌ حدث خطأ أثناء ضبط وقت النشر")
        return ConversationHandler.END

    await message.reply_text(f"✅ تم ضبط وقت النشر إلى {delay} ثانية")

    return ConversationHandler.END


# ==================================================
# CANCEL
# ==================================================

async def cancel_set_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await show_main_menu(update, context)
    elif update.message:
        await update.message.reply_text("❌ تم إلغاء ضبط وقت النشر")

    return ConversationHandler.END


# ==================================================
# BACK
# ==================================================

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await show_main_menu(update, context)
    elif update.message:
        await update.message.reply_text("🔙 تم الرجوع")

    return ConversationHandler.END


# ==================================================
# CONVERSATION
# ==================================================

def get_set_publish_delay_conversation():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_delay_start, pattern="^menu_set_delay$"),
        ],
        states={
            SET_DELAY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    set_delay_receive,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_set_delay, pattern="^cancel_set_delay$"),
            CallbackQueryHandler(back_main, pattern="^back_main$"),
            CommandHandler("cancel", cancel_set_delay),
        ],
        name="set_publish_delay_conversation",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=120,
    )
