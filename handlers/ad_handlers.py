import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADD_AD_TEXT, ADD_AD_MEDIA, AD_TYPES, MESSAGES

logger = logging.getLogger(__name__)


class AdHandlers:

    def __init__(self, db, manager):
        self.db = db
        self.manager = manager

    # ==================================================
    # MAIN MENU
    # ==================================================

    async def manage_ads(self, query, context):

        if not self.db.is_admin(query.from_user.id):
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
    # ADD AD START
    # ==================================================

    async def add_ad_start(self, query, context):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return ConversationHandler.END

        context.user_data.clear()

        keyboard = [
            [InlineKeyboardButton(AD_TYPES["text"], callback_data="ad_type_text")],
            [InlineKeyboardButton(AD_TYPES["photo"], callback_data="ad_type_photo")],
            [InlineKeyboardButton(AD_TYPES["contact"], callback_data="ad_type_contact")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")]
        ]

        await query.edit_message_text(
            "📢 اختر نوع الإعلان:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # AD TYPE
    # ==================================================

    async def add_ad_type(self, query, context):

        ad_type = query.data.replace("ad_type_", "")

        context.user_data.clear()
        context.user_data["ad_type"] = ad_type

        if ad_type == "contact":
            await query.edit_message_text("📞 أرسل جهة الاتصال أو ملف VCF الآن:")
            return ADD_AD_MEDIA

        await query.edit_message_text("📝 أرسل نص الإعلان الآن:")
        return ADD_AD_TEXT

    # ==================================================
    # AD TEXT
    # ==================================================

    async def add_ad_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.message.from_user.id
        ad_type = context.user_data.get("ad_type")

        if not ad_type:
            await update.message.reply_text("❌ لم يتم تحديد نوع الإعلان")
            return ConversationHandler.END

        text = update.message.text.strip()

        if len(text) < 2:
            await update.message.reply_text("❌ النص قصير جداً")
            return ADD_AD_TEXT

        # -------- TEXT ONLY --------

        if ad_type == "text":

            success, message = self.db.add_ad(
                "text",
                text,
                None,
                "text",
                user_id
            )

            if success:
                await update.message.reply_text("✅ تم إضافة الإعلان النصي بنجاح")
            else:
                await update.message.reply_text(f"❌ {message}")

            context.user_data.clear()
            return ConversationHandler.END

        # -------- PHOTO WITH TEXT --------

        context.user_data["ad_text"] = text
        await update.message.reply_text("🖼️ أرسل الصورة الآن:")
        return ADD_AD_MEDIA

    # ==================================================
    # MEDIA / CONTACT
    # ==================================================

    async def add_ad_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.message.from_user.id
        ad_type = context.user_data.get("ad_type")
        ad_text = context.user_data.get("ad_text", "")

        if not ad_type:
            await update.message.reply_text("❌ لم يتم تحديد نوع الإعلان")
            return ConversationHandler.END

        os.makedirs("temp_files/ads", exist_ok=True)

        success = False
        file_path = None

        # ---------- PHOTO ----------

        if update.message.photo:

            photo = update.message.photo[-1]
            file = await photo.get_file()

            name = f"photo_{int(datetime.now().timestamp())}.jpg"
            file_path = f"temp_files/ads/{name}"

            await file.download_to_drive(file_path)

            success, _ = self.db.add_ad(
                "photo",
                ad_text,
                file_path,
                "photo",
                user_id
            )

        # ---------- CONTACT FILE ----------

        elif update.message.document:

            file = await update.message.document.get_file()

            name = update.message.document.file_name or f"contact_{int(datetime.now().timestamp())}.vcf"
            file_path = f"temp_files/ads/{name}"

            await file.download_to_drive(file_path)

            success, _ = self.db.add_ad(
                "contact",
                None,
                file_path,
                "contact",
                user_id
            )

        # ---------- DIRECT CONTACT ----------

        elif update.message.contact:

            contact = update.message.contact

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
                "contact",
                user_id
            )

        else:
            await update.message.reply_text("❌ لم يتم التعرف على الملف")
            return ADD_AD_MEDIA

        if success:
            await update.message.reply_text("✅ تم إضافة الإعلان بنجاح")
        else:
            await update.message.reply_text("❌ فشل إضافة الإعلان")

        context.user_data.clear()
        return ConversationHandler.END

    # ==================================================
    # SHOW ADS
    # ==================================================

    async def show_ads(self, query, context):

        ads = self.db.get_ads(query.from_user.id)

        if not ads:
            await query.edit_message_text("❌ لا توجد إعلانات")
            return

        text = "📢 قائمة الإعلانات\n\n"
        keyboard = []

        for ad in ads[:15]:

            ad_id, ad_type, ad_text, media_path, _, added, _, _ = ad

            emoji = {
                "text": "📝",
                "photo": "🖼️",
                "contact": "📞"
            }.get(ad_type, "📄")

            text += f"#{ad_id} {emoji} {ad_type}\n"

            if ad_text:
                text += f"{ad_text[:40]}...\n"

            text += f"{added[:16]}\n──────────\n"

            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ حذف #{ad_id}",
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

    async def delete_ad(self, query, context, ad_id):

        if self.db.delete_ad(ad_id, query.from_user.id):
            await query.answer("✅ تم الحذف")
        else:
            await query.answer("❌ فشل الحذف")

        await self.show_ads(query, context)

    # ==================================================
    # STATS
    # ==================================================

    async def show_ad_stats(self, query, context):

        stats = self.db.get_statistics(query.from_user.id)
        ads = self.db.get_ads(query.from_user.id)

        count = {"text": 0, "photo": 0, "contact": 0}

        for ad in ads:
            if ad[1] in count:
                count[ad[1]] += 1

        text = (
            "📊 إحصائيات الإعلانات\n\n"
            f"📢 الإجمالي: {stats['ads']}\n\n"
            f"📝 النصية: {count['text']}\n"
            f"🖼️ الصور: {count['photo']}\n"
            f"📞 جهات الاتصال: {count['contact']}"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="ad_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
