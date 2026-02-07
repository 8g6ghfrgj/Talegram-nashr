from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from menus import show_ads_menu


class AdHandlers:

    def __init__(self, db):
        self.db = db


    # ==================================================
    # SHOW ADS
    # ==================================================

    async def show_ads(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()

        admin_id = query.from_user.id
        ads = self.db.get_ads(admin_id)

        if not ads:
            await query.edit_message_text(
                "❌ لا توجد إعلانات مضافة",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")]
                ])
            )
            return

        text = "📢 الإعلانات:\n\n"
        keyboard = []

        for ad in ads:
            ad_id, admin_id, ad_type, ad_text, ad_media, added = ad

            emoji = {
                "text": "📝",
                "photo": "🖼️",
                "contact": "📞"
            }.get(ad_type, "📄")

            text += f"#{ad_id} {emoji} {ad_type}\n"
            if ad_text:
                text += f"{ad_text[:40]}\n"
            text += f"{added}\n\n"

            keyboard.append([
                InlineKeyboardButton(
                    "🗑 حذف",
                    callback_data=f"delete_ad_{ad_id}"
                )
            ])

        keyboard.append(
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")]
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # DELETE AD
    # ==================================================

    async def delete_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id: int):

        query = update.callback_query
        await query.answer()

        admin_id = query.from_user.id
        self.db.delete_ad(ad_id, admin_id)

        await self.show_ads(update, context)


    # ==================================================
    # ADS STATS
    # ==================================================

    async def ad_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()

        admin_id = query.from_user.id
        ads = self.db.get_ads(admin_id)

        count = {"text": 0, "photo": 0, "contact": 0}

        for ad in ads:
            if ad[2] in count:
                count[ad[2]] += 1

        text = (
            "📊 إحصائيات الإعلانات\n\n"
            f"📢 الإجمالي: {len(ads)}\n"
            f"📝 نصية: {count['text']}\n"
            f"🖼️ صور: {count['photo']}\n"
            f"📞 جهات اتصال: {count['contact']}"
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")]
            ])
        )
