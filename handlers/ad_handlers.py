import os
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    ADD_AD_TYPE,
    ADD_AD_TEXT,
    ADD_AD_MEDIA,
    AD_TYPES,
    MESSAGES
)

logger = logging.getLogger(__name__)


class AdHandlers:

    def __init__(self, db, manager):
        self.db = db
        self.manager = manager


    # ==================================================
    # ADS MENU
    # ==================================================

    async def manage_ads(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        keyboard = [
            [InlineKeyboardButton("➕ إضافة إعلان", callback_data="add_ad")],
            [InlineKeyboardButton("📋 عرض الإعلانات", callback_data="show_ads")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="ad_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            "📢 إدارة الإعلانات",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # START ADD AD
    # ==================================================

    async def add_ad_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return ConversationHandler.END

        context.user_data.clear()

        keyboard = [
            [InlineKeyboardButton(AD_TYPES["text"], callback_data="ad_type_text")],
            [InlineKeyboardButton(AD_TYPES["photo"], callback_data="ad_type_photo")],
            [InlineKeyboardButton(AD_TYPES["contact"], callback_data="ad_type_contact")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_process")]
        ]

        await query.edit_message_text(
            "📢 اختر نوع الإعلان:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ADD_AD_TYPE


    # ==================================================
    # SELECT TYPE
    # ==================================================

    async def add_ad_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query

        ad_type = query.data.replace("ad_type_", "")

        context.user_data.clear()
        context.user_data["ad_type"] = ad_type

        keyboard = [
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_process")]
        ]

        if ad_type == "contact":
            await query.edit_message_text(
                "📞 أرسل جهة الاتصال أو ملف VCF:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ADD_AD_MEDIA

        await query.edit_message_text(
            "📝 أرسل نص الإعلان:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADD_AD_TEXT


    # ==================================================
    # TEXT STEP
    # ==================================================

    async def add_ad_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        message = update.message
        user_id = message.from_user.id

        ad_type = context.user_data.get("ad_type")

        if not ad_type:
            await message.reply_text("❌ لم يتم تحديد نوع الإعلان")
            return ConversationHandler.END

        text = message.text.strip()

        if len(text) < 2:
            await message.reply_text("❌ النص قصير جداً")
            return ADD_AD_TEXT


        # -------- TEXT ONLY --------

        if ad_type == "text":

            success, msg = self.db.add_ad(
                "text",
                text,
                None,
                None,
                user_id
            )

            if success:
                await message.reply_text("✅ تم إضافة الإعلان النصي بنجاح")
            else:
                await message.reply_text(f"❌ {msg}")

            context.user_data.clear()
            return ConversationHandler.END


        # -------- PHOTO NEED --------

        context.user_data["ad_text"] = text

        keyboard = [
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_process")]
        ]

        await message.reply_text(
            "🖼️ أرسل الصورة الآن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ADD_AD_MEDIA


    # ==================================================
    # MEDIA / CONTACT
    # ==================================================

    async def add_ad_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        message = update.message
        user_id = message.from_user.id

        ad_type = context.user_data.get("ad_type")
        ad_text = context.user_data.get("ad_text")

        if not ad_type:
            await message.reply_text("❌ لم يتم تحديد نوع الإعلان")
            return ConversationHandler.END

        os.makedirs("temp_files/ads", exist_ok=True)

        success = False
        file_path = None


        # ---------- PHOTO ----------

        if message.photo:

            photo = message.photo[-1]
            file = await photo.get_file()

            name = f"photo_{int(datetime.now().timestamp())}.jpg"
            file_path = f"temp_files/ads/{name}"

            await file.download_to_drive(file_path)

            success, _ = self.db.add_ad(
                "photo",
                ad_text,
                file_path,
                None,
                user_id
            )


        # ---------- CONTACT FILE ----------

        elif message.document:

            file = await message.document.get_file()

            name = message.document.file_name or f"contact_{int(datetime.now().timestamp())}.vcf"
            file_path = f"temp_files/ads/{name}"

            await file.download_to_drive(file_path)

            success, _ = self.db.add_ad(
                "contact",
                None,
                file_path,
                None,
                user_id
            )


        # ---------- DIRECT CONTACT ----------

        elif message.contact:

            contact = message.contact

            name = f"contact_{int(datetime.now().timestamp())}.vcf"
            file_path = f"temp_files/ads/{name}"

            vcf = (
                "BEGIN:VCARD\n"
                "VERSION:3.0\n"
                f"FN:{contact.first_name}\n"
                f"TEL:{contact.phone_number}\n"
                "END:VCARD"
            )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(vcf)

            success, _ = self.db.add_ad(
                "contact",
                None,
                file_path,
                None,
                user_id
            )

        else:
            await message.reply_text("❌ نوع غير مدعوم")
            return ADD_AD_MEDIA


        if success:
            await message.reply_text("✅ تم إضافة الإعلان بنجاح")
        else:
            await message.reply_text("❌ فشل إضافة الإعلان")

        context.user_data.clear()
        return ConversationHandler.END


    # ==================================================
    # SHOW ADS
    # ==================================================

    async def show_ads(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        ads = self.db.get_ads(user_id)

        if not ads:
            await query.edit_message_text("❌ لا توجد إعلانات")
            return

        text = "📢 قائمة الإعلانات:\n\n"
        keyboard = []

        for ad in ads[:15]:

            # DB schema:
            # id, admin_id, type, text, media, added
            ad_id, admin_id, ad_type, ad_text, media, added = ad

            emoji = {
                "text": "📝",
                "photo": "🖼️",
                "contact": "📞"
            }.get(ad_type, "📄")

            text += f"#{ad_id} {emoji} {ad_type}\n"

            if ad_text:
                text += f"{ad_text[:40]}...\n"

            text += f"{added}\n──────────\n"

            keyboard.append([
                InlineKeyboardButton(
                    "🗑 حذف",
                    callback_data=f"delete_ad_{ad_id}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton("🔄 تحديث", callback_data="show_ads"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")
        ])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # DELETE AD
    # ==================================================

    async def delete_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id: int):

        query = update.callback_query
        user_id = query.from_user.id

        if self.db.delete_ad(ad_id, user_id):
            await query.answer("✅ تم حذف الإعلان")
        else:
            await query.answer("❌ فشل الحذف")

        await self.show_ads(update, context)


    # ==================================================
    # STATS
    # ==================================================

    async def show_ad_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        ads = self.db.get_ads(user_id)

        total = len(ads)
        text_ads = len([a for a in ads if a[2] == "text"])
        photo_ads = len([a for a in ads if a[2] == "photo"])
        contact_ads = len([a for a in ads if a[2] == "contact"])

        text = (
            "📊 إحصائيات الإعلانات\n\n"
            f"📢 الإجمالي: {total}\n\n"
            f"📝 النصية: {text_ads}\n"
            f"🖼️ الصور: {photo_ads}\n"
            f"📞 جهات الاتصال: {contact_ads}"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="ad_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
