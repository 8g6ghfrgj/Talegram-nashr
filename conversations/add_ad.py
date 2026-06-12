import os
import uuid
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import ADD_AD_TYPE, ADD_AD_TEXT, ADD_AD_MEDIA
from menus import show_ads_menu


# ==================================================
# CONSTANTS
# ==================================================

ADS_DIR = "temp_files/ads"
MIN_AD_TEXT_LENGTH = 2

ADD_AD_USER_DATA_KEYS = (
    "ad_type",
    "ad_text",
)

ALLOWED_AD_TYPES = {
    "text",
    "photo",
    "contact",
}


# ==================================================
# HELPERS
# ==================================================

def clear_add_ad_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    حذف بيانات إضافة الإعلان فقط بدون حذف باقي بيانات المستخدم.
    """
    for key in ADD_AD_USER_DATA_KEYS:
        context.user_data.pop(key, None)


def get_cancel_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_ad")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")],
    ])


def ensure_ads_dir() -> None:
    os.makedirs(ADS_DIR, exist_ok=True)


def make_unique_file_path(prefix: str, extension: str) -> str:
    """
    إنشاء اسم ملف فريد لتجنب استبدال الملفات السابقة.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_part = uuid.uuid4().hex[:8]
    return os.path.join(ADS_DIR, f"{prefix}_{timestamp}_{random_part}{extension}")


def safe_document_name(file_name: str | None) -> str:
    """
    منع path traversal عند حفظ اسم ملف قادم من المستخدم.
    """
    if not file_name:
        file_name = "contact.vcf"

    file_name = os.path.basename(file_name)
    file_name = file_name.replace("/", "_").replace("\\", "_").strip()

    if not file_name:
        file_name = "contact.vcf"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_part = uuid.uuid4().hex[:8]

    name, ext = os.path.splitext(file_name)

    if not ext:
        ext = ".vcf"

    return f"{name}_{timestamp}_{random_part}{ext}"


def get_db(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data.get("db")


# ==================================================
# START ADD AD
# ==================================================

async def add_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    clear_add_ad_data(context)

    keyboard = [
        [InlineKeyboardButton("📝 نص فقط", callback_data="ad_type_text")],
        [InlineKeyboardButton("🖼️ صورة مع نص", callback_data="ad_type_photo")],
        [InlineKeyboardButton("📞 جهة اتصال", callback_data="ad_type_contact")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_ad")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")],
    ]

    await query.edit_message_text(
        "📢 اختر نوع الإعلان:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADD_AD_TYPE


# ==================================================
# SELECT TYPE
# ==================================================

async def add_ad_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await query.answer()

    callback_data = query.data or ""

    if not callback_data.startswith("ad_type_"):
        await query.edit_message_text("❌ نوع الإعلان غير صحيح")
        clear_add_ad_data(context)
        return ConversationHandler.END

    ad_type = callback_data.replace("ad_type_", "", 1)

    if ad_type not in ALLOWED_AD_TYPES:
        await query.edit_message_text("❌ نوع الإعلان غير مدعوم")
        clear_add_ad_data(context)
        return ConversationHandler.END

    context.user_data["ad_type"] = ad_type

    if ad_type == "contact":
        await query.edit_message_text(
            "📞 أرسل جهة الاتصال الآن:",
            reply_markup=get_cancel_back_keyboard(),
        )
        return ADD_AD_MEDIA

    await query.edit_message_text(
        "📝 أرسل نص الإعلان:",
        reply_markup=get_cancel_back_keyboard(),
    )

    return ADD_AD_TEXT


# ==================================================
# RECEIVE TEXT
# ==================================================

async def add_ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return ADD_AD_TEXT

    text = message.text.strip()
    ad_type = context.user_data.get("ad_type")

    if ad_type not in ("text", "photo"):
        await message.reply_text("❌ نوع الإعلان غير معروف، أعد المحاولة")
        clear_add_ad_data(context)
        return ConversationHandler.END

    if len(text) < MIN_AD_TEXT_LENGTH:
        await message.reply_text("❌ النص قصير جدًا")
        return ADD_AD_TEXT

    db = get_db(context)

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        clear_add_ad_data(context)
        return ConversationHandler.END

    # نص فقط
    if ad_type == "text":
        try:
            db.add_ad(
                admin_id=update.effective_user.id,
                ad_type="text",
                text=text,
                media_path=None,
            )
        except Exception:
            await message.reply_text("❌ حدث خطأ أثناء إضافة الإعلان")
            clear_add_ad_data(context)
            return ConversationHandler.END

        await message.reply_text("✅ تم إضافة الإعلان النصي")
        clear_add_ad_data(context)
        return ConversationHandler.END

    # صورة + نص
    context.user_data["ad_text"] = text

    await message.reply_text(
        "🖼️ أرسل الصورة الآن:",
        reply_markup=get_cancel_back_keyboard(),
    )

    return ADD_AD_MEDIA


# ==================================================
# RECEIVE MEDIA / CONTACT
# ==================================================

async def add_ad_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return ADD_AD_MEDIA

    db = get_db(context)

    if db is None:
        await message.reply_text("❌ خطأ داخلي: قاعدة البيانات غير مهيأة")
        clear_add_ad_data(context)
        return ConversationHandler.END

    if not update.effective_user:
        await message.reply_text("❌ تعذر تحديد المستخدم")
        clear_add_ad_data(context)
        return ConversationHandler.END

    user_id = update.effective_user.id
    ad_type = context.user_data.get("ad_type")
    ad_text = context.user_data.get("ad_text", "")

    ensure_ads_dir()

    # ==================================================
    # PHOTO AD
    # ==================================================

    if ad_type == "photo":
        if not message.photo:
            await message.reply_text("❌ أرسل صورة فقط")
            return ADD_AD_MEDIA

        try:
            photo = message.photo[-1]
            file = await photo.get_file()

            file_path = make_unique_file_path("photo", ".jpg")
            await file.download_to_drive(file_path)

            db.add_ad(
                admin_id=user_id,
                ad_type="photo",
                text=ad_text,
                media_path=file_path,
            )

        except Exception:
            await message.reply_text("❌ حدث خطأ أثناء حفظ إعلان الصورة")
            clear_add_ad_data(context)
            return ConversationHandler.END

        await message.reply_text("✅ تم إضافة إعلان الصورة")
        clear_add_ad_data(context)
        return ConversationHandler.END

    # ==================================================
    # CONTACT AD
    # ==================================================

    if ad_type == "contact":

        # CONTACT FILE
        if message.document:
            try:
                document = message.document
                file = await document.get_file()

                safe_name = safe_document_name(document.file_name)
                file_path = os.path.join(ADS_DIR, safe_name)

                await file.download_to_drive(file_path)

                db.add_ad(
                    admin_id=user_id,
                    ad_type="contact",
                    text="",
                    media_path=file_path,
                )

            except Exception:
                await message.reply_text("❌ حدث خطأ أثناء حفظ ملف جهة الاتصال")
                clear_add_ad_data(context)
                return ConversationHandler.END

            await message.reply_text("✅ تم إضافة جهة الاتصال")
            clear_add_ad_data(context)
            return ConversationHandler.END

        # DIRECT CONTACT
        if message.contact:
            try:
                contact = message.contact

                file_path = make_unique_file_path("contact", ".vcf")

                first_name = contact.first_name or "Contact"
                last_name = contact.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                phone_number = contact.phone_number or ""

                vcf = (
                    "BEGIN:VCARD\n"
                    "VERSION:3.0\n"
                    f"FN:{full_name}\n"
                    f"N:{last_name};{first_name};;;\n"
                    f"TEL:{phone_number}\n"
                    "END:VCARD\n"
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(vcf)

                db.add_ad(
                    admin_id=user_id,
                    ad_type="contact",
                    text="",
                    media_path=file_path,
                )

            except Exception:
                await message.reply_text("❌ حدث خطأ أثناء حفظ جهة الاتصال")
                clear_add_ad_data(context)
                return ConversationHandler.END

            await message.reply_text("✅ تم إضافة جهة الاتصال")
            clear_add_ad_data(context)
            return ConversationHandler.END

        await message.reply_text("❌ أرسل جهة اتصال أو ملف جهة اتصال")
        return ADD_AD_MEDIA

    # ==================================================
    # UNKNOWN TYPE
    # ==================================================

    await message.reply_text("❌ نوع الإعلان غير معروف، أعد المحاولة")
    clear_add_ad_data(context)
    return ConversationHandler.END


# ==================================================
# CANCEL
# ==================================================

async def cancel_add_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_add_ad_data(context)

    if update.callback_query:
        await update.callback_query.answer()
        await show_ads_menu(update, context)
    elif update.message:
        await update.message.reply_text("❌ تم إلغاء إضافة الإعلان")

    return ConversationHandler.END


# ==================================================
# BACK
# ==================================================

async def back_to_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_add_ad_data(context)

    if update.callback_query:
        await update.callback_query.answer()
        await show_ads_menu(update, context)
    elif update.message:
        await update.message.reply_text("🔙 تم الرجوع")

    return ConversationHandler.END


# ==================================================
# CONVERSATION HANDLER
# ==================================================

def get_add_ad_conversation():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_ad_start, pattern="^add_ad$"),
        ],
        states={
            ADD_AD_TYPE: [
                CallbackQueryHandler(add_ad_type, pattern="^ad_type_"),
            ],
            ADD_AD_TEXT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_ad_text,
                ),
            ],
            ADD_AD_MEDIA: [
                MessageHandler(
                    filters.PHOTO | filters.Document.ALL | filters.CONTACT,
                    add_ad_media,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_ad, pattern="^cancel_add_ad$"),
            CallbackQueryHandler(back_to_ads, pattern="^back_ads$"),
            CommandHandler("cancel", cancel_add_ad),
        ],
        name="add_ad_conversation",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=180,
    )
