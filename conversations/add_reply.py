import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import ADD_PRIVATE_TEXT, ADD_RANDOM_REPLY
from menus import show_replies_menu


# ==================================================
# START MENU
# ==================================================

async def add_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💬 رد خاص (نص)", callback_data="reply_private")],
        [InlineKeyboardButton("🎲 رد عشوائي", callback_data="reply_random")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
    ]

    await query.edit_message_text(
        "💬 اختر نوع الرد:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# PRIVATE REPLY
# ==================================================

async def add_private_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["reply_type"] = "private"

    await query.edit_message_text(
        "✏️ أرسل نص الرد الخاص:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
        ])
    )

    return ADD_PRIVATE_TEXT


async def add_private_reply_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()
    db = context.application.bot_data["db"]
    user_id = update.effective_user.id

    if len(text) < 2:
        await update.message.reply_text("❌ النص قصير جدًا")
        return ADD_PRIVATE_TEXT

    db.add_private_reply(user_id, text)
    await update.message.reply_text("✅ تم إضافة الرد الخاص")

    context.user_data.clear()
    return ConversationHandler.END


# ==================================================
# RANDOM REPLY
# ==================================================

async def add_random_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["reply_type"] = "random"

    keyboard = [
        [InlineKeyboardButton("📝 نص فقط", callback_data="random_text")],
        [InlineKeyboardButton("🖼️ صورة + نص", callback_data="random_photo")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
    ]

    await query.edit_message_text(
        "🎲 اختر نوع الرد العشوائي:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_random_reply_type(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    r_type = query.data.replace("random_", "")
    context.user_data["random_type"] = r_type

    await query.edit_message_text(
        "✏️ أرسل نص الرد (أو اضغط Skip لتخطي النص):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Skip", callback_data="skip_text")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
        ])
    )

    return ADD_RANDOM_REPLY


async def add_random_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["text"] = update.message.text.strip()

    await update.message.reply_text(
        "🖼️ أرسل الصورة الآن (أو اضغط Skip لتخطي الصورة):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Skip", callback_data="skip_media")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
        ])
    )

    return ADD_RANDOM_REPLY


async def add_random_reply_media(update: Update, context: ContextTypes.DEFAULT_TYPE):

    db = context.application.bot_data["db"]
    user_id = update.effective_user.id

    text = context.user_data.get("text")
    r_type = context.user_data.get("random_type")

    media_path = None

    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()

        os.makedirs("temp_files/random_replies", exist_ok=True)
        media_path = f"temp_files/random_replies/{int(datetime.now().timestamp())}.jpg"
        await file.download_to_drive(media_path)

    db.add_random_reply(user_id, r_type, text, media_path)
    await update.message.reply_text("✅ تم إضافة الرد العشوائي")

    context.user_data.clear()
    return ConversationHandler.END


# ==================================================
# SKIP HANDLERS
# ==================================================

async def skip_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["text"] = None

    await query.edit_message_text(
        "🖼️ أرسل الصورة الآن (أو اضغط Skip لتخطي الصورة):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Skip", callback_data="skip_media")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
        ])
    )

    return ADD_RANDOM_REPLY


async def skip_media(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    db = context.application.bot_data["db"]
    user_id = query.from_user.id

    text = context.user_data.get("text")
    r_type = context.user_data.get("random_type")

    db.add_random_reply(user_id, r_type, text, None)

    await query.edit_message_text("✅ تم إضافة الرد العشوائي")
    context.user_data.clear()
    return ConversationHandler.END


# ==================================================
# CANCEL & BACK
# ==================================================

async def cancel_add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    if update.callback_query:
        await update.callback_query.answer()
        await show_replies_menu(update, context)

    return ConversationHandler.END


async def back_to_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    if update.callback_query:
        await update.callback_query.answer()
        await show_replies_menu(update, context)

    return ConversationHandler.END


# ==================================================
# CONVERSATION HANDLER
# ==================================================

def get_add_reply_conversation():

    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_reply_start, pattern="^add_private_reply$|^add_random_reply$")
        ],
        states={
            ADD_PRIVATE_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_private_reply_receive)
            ],
            ADD_RANDOM_REPLY: [
                CallbackQueryHandler(add_private_reply_start, pattern="^reply_private$"),
                CallbackQueryHandler(add_random_reply_start, pattern="^reply_random$"),
                CallbackQueryHandler(add_random_reply_type, pattern="^random_"),
                CallbackQueryHandler(skip_text, pattern="^skip_text$"),
                CallbackQueryHandler(skip_media, pattern="^skip_media$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_random_reply_text),
                MessageHandler(filters.PHOTO, add_random_reply_media)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_reply, pattern="^cancel_add_reply$"),
            CallbackQueryHandler(back_to_replies, pattern="^back_replies$")
        ],
        name="add_reply_conversation",
        persistent=False
  )
