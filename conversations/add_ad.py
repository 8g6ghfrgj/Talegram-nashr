import os
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import ADD_AD_TYPE, ADD_AD_TEXT, ADD_AD_MEDIA
from menus import show_ads_menu


# ==================================================
# START ADD AD
# ==================================================

async def add_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("📝 نص فقط", callback_data="ad_type_text")],
        [InlineKeyboardButton("🖼️ صورة مع نص", callback_data="ad_type_photo")],
        [InlineKeyboardButton("📞 جهة اتصال", callback_data="ad_type_contact")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_ad")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")]
    ]

    await query.edit_message_text(
        "📢 اختر نوع الإعلان:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADD_AD_TYPE


# ==================================================
# SELECT TYPE
# ==================================================

async def add_ad_type(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    ad_type = query.data.replace("ad_type_", "")
    context.user_data["ad_type"] = ad_type

    if ad_type == "contact":
        await query.edit_message_text(
            "📞 أرسل جهة الاتصال الآن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_ad")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")]
            ])
        )
        return ADD_AD_MEDIA

    await query.edit_message_text(
        "📝 أرسل نص الإعلان:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_ad")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")]
        ])
    )
    return ADD_AD_TEXT


# ==================================================
# RECEIVE TEXT
# ==================================================

async def add_ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()
    ad_type = context.user_data.get("ad_type")

    if len(text) < 2:
        await update.message.reply_text("❌ النص قصير جدًا")
        return ADD_AD_TEXT

    # نص فقط
    if ad_type == "text":
        db = context.application.bot_data["db"]
        db.add_ad(
            admin_id=update.effective_user.id,
            ad_type="text",
            text=text,
            media_path=None
        )
        await update.message.reply_text("✅ تم إضافة الإعلان النصي")
        context.user_data.clear()
        return ConversationHandler.END

    # صورة + نص
    context.user_data["ad_text"] = text
    await update.message.reply_text(
        "🖼️ أرسل الصورة الآن:"
    )
    return ADD_AD_MEDIA


# ==================================================
# RECEIVE MEDIA / CONTACT
# ==================================================

async def add_ad_media(update: Update, context: ContextTypes.DEFAULT_TYPE):

    db = context.application.bot_data["db"]
    user_id = update.effective_user.id
    ad_type = context.user_data.get("ad_type")
    ad_text = context.user_data.get("ad_text")

    os.makedirs("temp_files/ads", exist_ok=True)
    file_path = None

    # PHOTO
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"temp_files/ads/photo_{int(datetime.now().timestamp())}.jpg"
        await file.download_to_drive(file_path)

        db.add_ad(
            admin_id=user_id,
            ad_type="photo",
            text=ad_text,
            media_path=file_path
        )
        await update.message.reply_text("✅ تم إضافة إعلان الصورة")

    # CONTACT FILE
    elif update.message.document:
        file = await update.message.document.get_file()
        file_path = f"temp_files/ads/{update.message.document.file_name}"
        await file.download_to_drive(file_path)

        db.add_ad(
            admin_id=user_id,
            ad_type="contact",
            text="",
            media_path=file_path
        )
        await update.message.reply_text("✅ تم إضافة جهة الاتصال")

    # DIRECT CONTACT
    elif update.message.contact:
        contact = update.message.contact
        file_path = f"temp_files/ads/contact_{int(datetime.now().timestamp())}.vcf"

        vcf = (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"FN:{contact.first_name}\n"
            f"TEL:{contact.phone_number}\n"
            "END:VCARD"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(vcf)

        db.add_ad(
            admin_id=user_id,
            ad_type="contact",
            text="",
            media_path=file_path
        )
        await update.message.reply_text("✅ تم إضافة جهة الاتصال")

    else:
        await update.message.reply_text("❌ لم يتم التعرف على الملف")
        return ADD_AD_MEDIA

    context.user_data.clear()
    return ConversationHandler.END


# ==================================================
# CANCEL
# ==================================================

async def cancel_add_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    if update.callback_query:
        await update.callback_query.answer()
        await show_ads_menu(update, context)

    return ConversationHandler.END


# ==================================================
# BACK
# ==================================================

async def back_to_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    if update.callback_query:
        await update.callback_query.answer()
        await show_ads_menu(update, context)

    return ConversationHandler.END


# ==================================================
# CONVERSATION HANDLER
# ==================================================

def get_add_ad_conversation():

    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_ad_start, pattern="^add_ad$")
        ],
        states={
            ADD_AD_TYPE: [
                CallbackQueryHandler(add_ad_type, pattern="^ad_type_")
            ],
            ADD_AD_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_ad_text)
            ],
            ADD_AD_MEDIA: [
                MessageHandler(
                    filters.PHOTO | filters.Document.ALL | filters.CONTACT,
                    add_ad_media
                )
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_ad, pattern="^cancel_add_ad$"),
            CallbackQueryHandler(back_to_ads, pattern="^back_ads$")
        ],
        name="add_ad_conversation",
        persistent=False
    )
