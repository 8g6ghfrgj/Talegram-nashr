import os
import uuid
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import ADD_PRIVATE_TEXT, ADD_RANDOM_REPLY
from menus import show_replies_menu


# ==================================================
# CONSTANTS
# ==================================================

RANDOM_REPLIES_DIR = "temp_files/random_replies"
MIN_TEXT_LENGTH = 2

ADD_REPLY_USER_DATA_KEYS = (
    "reply_type",
    "random_type",
    "text",
)


# ==================================================
# HELPERS
# ==================================================

def clear_add_reply_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    حذف بيانات إضافة الرد فقط بدون حذف باقي بيانات المستخدم.
    """
    for key in ADD_REPLY_USER_DATA_KEYS:
        context.user_data.pop(key, None)


def get_cancel_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")],
    ])


def get_skip_text_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Skip", callback_data="skip_text")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")],
    ])


def get_skip_media_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Skip", callback_data="skip_media")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")],
    ])


def get_db(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data.get("db")


def ensure_random_replies_dir() -> None:
    os.makedirs(RANDOM_REPLIES_DIR, exist_ok=True)


def make_photo_path() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_part = uuid.uuid4().hex[:8]
    return os.path.join(
        RANDOM_REPLIES_DIR,
        f"reply_{timestamp}_{random_part}.jpg",
    )


# ==================================================
# START MENU
# ==================================================

async def add_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    clear_add_reply_data(context)

    keyboard = [
        [InlineKeyboardButton("💬 رد خاص (نص)", callback_data="reply_private")],
        [InlineKeyboardButton("🎲 رد عشوائي", callback_data="reply_random")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")],
    ]

    await query.edit_message_text(
        "💬 اختر نوع الرد:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADD_RANDOM_REPLY


# ==================================================
# PRIVATE REPLY
# ==================================================

async def add_private_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    clear_add_reply_data(context)
    context.user_data["reply_type"] = "private"

    await query.edit_message_text(
        "✏️ أرسل نص الرد الخاص:",
        reply_markup=get_cancel_back_keyboard(),
    )

    return ADD_PRIVATE_TEXT


async def add_private_reply_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return ADD_PRIVATE_TEXT

    user = update.effective_user

    if not user:
        await message.reply_text("❌ تعذر تحديد المستخدم")
        clear_add_reply_data(context)
        return ConversationHandler.END

    text = message.text.strip()

    if len(text) < MIN_TEXT_LENGTH:
        await message.reply_text("❌ النص قصير جدًا")
        return ADD_PRIVATE_TEXT

    db = get_db(context)

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        clear_add_reply_data(context)
        return ConversationHandler.END

    try:
        db.add_private_reply(user.id, text)
    except Exception:
        await message.reply_text("❌ حدث خطأ أثناء إضافة الرد الخاص")
        clear_add_reply_data(context)
        return ConversationHandler.END

    await message.reply_text("✅ تم إضافة الرد الخاص")

    clear_add_reply_data(context)
    return ConversationHandler.END


# ==================================================
# RANDOM REPLY
# ==================================================

async def add_random_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    clear_add_reply_data(context)
    context.user_data["reply_type"] = "random"

    keyboard = [
        [InlineKeyboardButton("📝 نص فقط", callback_data="random_text")],
        [InlineKeyboardButton("🖼️ صورة + نص", callback_data="random_photo")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_reply")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")],
    ]

    await query.edit_message_text(
        "🎲 اختر نوع الرد العشوائي:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADD_RANDOM_REPLY


async def add_random_reply_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    callback_data = query.data or ""
    r_type = callback_data.replace("random_", "", 1)

    if r_type not in ("text", "photo"):
        await query.edit_message_text("❌ نوع الرد غير مدعوم")
        clear_add_reply_data(context)
        return ConversationHandler.END

    context.user_data["random_type"] = r_type

    if r_type == "text":
        await query.edit_message_text(
            "✏️ أرسل نص الرد العشوائي:",
            reply_markup=get_cancel_back_keyboard(),
        )
    else:
        await query.edit_message_text(
            "✏️ أرسل نص الرد أو اضغط Skip لتخطي النص:",
            reply_markup=get_skip_text_keyboard(),
        )

    return ADD_RANDOM_REPLY


async def add_random_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return ADD_RANDOM_REPLY

    user = update.effective_user

    if not user:
        await message.reply_text("❌ تعذر تحديد المستخدم")
        clear_add_reply_data(context)
        return ConversationHandler.END

    r_type = context.user_data.get("random_type")
    text = message.text.strip()

    if r_type not in ("text", "photo"):
        await message.reply_text("❌ نوع الرد غير معروف، أعد المحاولة")
        clear_add_reply_data(context)
        return ConversationHandler.END

    if len(text) < MIN_TEXT_LENGTH:
        await message.reply_text("❌ النص قصير جدًا")
        return ADD_RANDOM_REPLY

    db = get_db(context)

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        clear_add_reply_data(context)
        return ConversationHandler.END

    # رد عشوائي نص فقط
    if r_type == "text":
        try:
            db.add_random_reply(
                user.id,
                "text",
                text,
                None,
            )
        except Exception:
            await message.reply_text("❌ حدث خطأ أثناء إضافة الرد العشوائي")
            clear_add_reply_data(context)
            return ConversationHandler.END

        await message.reply_text("✅ تم إضافة الرد العشوائي")
        clear_add_reply_data(context)
        return ConversationHandler.END

    # رد عشوائي صورة + نص
    context.user_data["text"] = text

    await message.reply_text(
        "🖼️ أرسل الصورة الآن أو اضغط Skip لتخطي الصورة:",
        reply_markup=get_skip_media_keyboard(),
    )

    return ADD_RANDOM_REPLY


async def add_random_reply_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return ADD_RANDOM_REPLY

    user = update.effective_user

    if not user:
        await message.reply_text("❌ تعذر تحديد المستخدم")
        clear_add_reply_data(context)
        return ConversationHandler.END

    r_type = context.user_data.get("random_type")

    if r_type != "photo":
        await message.reply_text("❌ هذا النوع يقبل نصًا فقط")
        return ADD_RANDOM_REPLY

    if not message.photo:
        await message.reply_text("❌ أرسل صورة صحيحة")
        return ADD_RANDOM_REPLY

    db = get_db(context)

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        clear_add_reply_data(context)
        return ConversationHandler.END

    text = context.user_data.get("text")
    media_path = None

    try:
        ensure_random_replies_dir()

        photo = message.photo[-1]
        file = await photo.get_file()

        media_path = make_photo_path()
        await file.download_to_drive(media_path)

        db.add_random_reply(
            user.id,
            "photo",
            text,
            media_path,
        )

    except Exception:
        await message.reply_text("❌ حدث خطأ أثناء إضافة الرد العشوائي")
        clear_add_reply_data(context)
        return ConversationHandler.END

    await message.reply_text("✅ تم إضافة الرد العشوائي")

    clear_add_reply_data(context)
    return ConversationHandler.END


# ==================================================
# SKIP HANDLERS
# ==================================================

async def skip_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    r_type = context.user_data.get("random_type")

    if r_type != "photo":
        await query.edit_message_text(
            "❌ لا يمكن تخطي النص في رد نصي فقط.",
            reply_markup=get_cancel_back_keyboard(),
        )
        return ADD_RANDOM_REPLY

    context.user_data["text"] = None

    await query.edit_message_text(
        "🖼️ أرسل الصورة الآن:",
        reply_markup=get_cancel_back_keyboard(),
    )

    return ADD_RANDOM_REPLY


async def skip_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    user = query.from_user

    if not user:
        await query.edit_message_text("❌ تعذر تحديد المستخدم")
        clear_add_reply_data(context)
        return ConversationHandler.END

    r_type = context.user_data.get("random_type")
    text = context.user_data.get("text")

    if r_type != "photo":
        await query.edit_message_text("❌ لا يمكن تخطي الصورة لهذا النوع")
        clear_add_reply_data(context)
        return ConversationHandler.END

    if not text:
        await query.edit_message_text(
            "❌ لا يمكن حفظ رد فارغ. أرسل نصًا أو صورة.",
            reply_markup=get_cancel_back_keyboard(),
        )
        return ADD_RANDOM_REPLY

    db = get_db(context)

    if db is None:
        await query.edit_message_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        clear_add_reply_data(context)
        return ConversationHandler.END

    try:
        db.add_random_reply(
            user.id,
            "photo",
            text,
            None,
        )
    except Exception:
        await query.edit_message_text("❌ حدث خطأ أثناء إضافة الرد العشوائي")
        clear_add_reply_data(context)
        return ConversationHandler.END

    await query.edit_message_text("✅ تم إضافة الرد العشوائي")

    clear_add_reply_data(context)
    return ConversationHandler.END


# ==================================================
# CANCEL & BACK
# ==================================================

async def cancel_add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_add_reply_data(context)

    if update.callback_query:
        await update.callback_query.answer()
        await show_replies_menu(update, context)
    elif update.message:
        await update.message.reply_text("❌ تم إلغاء إضافة الرد")

    return ConversationHandler.END


async def back_to_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_add_reply_data(context)

    if update.callback_query:
        await update.callback_query.answer()
        await show_replies_menu(update, context)
    elif update.message:
        await update.message.reply_text("🔙 تم الرجوع")

    return ConversationHandler.END


# ==================================================
# CONVERSATION HANDLER
# ==================================================

def get_add_reply_conversation():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                add_reply_start,
                pattern="^add_private_reply$|^add_random_reply$|^add_reply$",
            ),
        ],
        states={
            ADD_PRIVATE_TEXT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_private_reply_receive,
                ),
            ],
            ADD_RANDOM_REPLY: [
                CallbackQueryHandler(add_private_reply_start, pattern="^reply_private$"),
                CallbackQueryHandler(add_random_reply_start, pattern="^reply_random$"),
                CallbackQueryHandler(add_random_reply_type, pattern="^random_"),
                CallbackQueryHandler(skip_text, pattern="^skip_text$"),
                CallbackQueryHandler(skip_media, pattern="^skip_media$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_random_reply_text),
                MessageHandler(filters.PHOTO, add_random_reply_media),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_reply, pattern="^cancel_add_reply$"),
            CallbackQueryHandler(back_to_replies, pattern="^back_replies$"),
            CommandHandler("cancel", cancel_add_reply),
        ],
        name="add_reply_conversation",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=180,
    )
