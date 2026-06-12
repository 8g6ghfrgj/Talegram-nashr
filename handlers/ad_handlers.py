from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


class AdHandlers:
    def __init__(self, db):
        self.db = db

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _back_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")]
        ])

    @staticmethod
    def _get_ad_value(ad, key: str, index: int, default=None):
        """
        يدعم sqlite3.Row أو tuple/list.
        """
        try:
            return ad[key]
        except Exception:
            try:
                return ad[index]
            except Exception:
                return default

    @staticmethod
    def _get_ad_emoji(ad_type: str) -> str:
        return {
            "text": "📝",
            "photo": "🖼️",
            "contact": "📞",
        }.get(ad_type, "📄")

    @staticmethod
    def _short_text(text: str | None, limit: int = 40) -> str:
        if not text:
            return ""

        text = text.strip()

        if len(text) <= limit:
            return text

        return text[:limit] + "..."

    def _build_ads_view(self, ads):
        if not ads:
            return (
                "❌ لا توجد إعلانات مضافة",
                self._back_keyboard(),
            )

        text = "📢 الإعلانات:\n\n"
        keyboard = []

        for ad in ads:
            ad_id = self._get_ad_value(ad, "id", 0)
            ad_type = self._get_ad_value(ad, "type", 2, "unknown")
            ad_text = self._get_ad_value(ad, "text", 3, "")
            active = self._get_ad_value(ad, "active", 5, 1)
            added_at = self._get_ad_value(ad, "added_at", 6, "")

            emoji = self._get_ad_emoji(ad_type)
            status = "✅ نشط" if active == 1 else "⛔ معطل"

            text += f"#{ad_id} {emoji} {ad_type} — {status}\n"

            short_text = self._short_text(ad_text)
            if short_text:
                text += f"{short_text}\n"

            if added_at:
                text += f"📅 {added_at}\n"

            text += "\n"

            keyboard.append([
                InlineKeyboardButton(
                    "🗑 حذف",
                    callback_data=f"delete_ad_{ad_id}",
                )
            ])

        keyboard.append([
            InlineKeyboardButton("🔙 رجوع", callback_data="back_ads")
        ])

        return text, InlineKeyboardMarkup(keyboard)

    async def _send_ads_view(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        notice: str | None = None,
        answer_query: bool = True,
    ):
        query = update.callback_query

        if not query:
            return

        if answer_query:
            await query.answer()

        admin_id = query.from_user.id

        try:
            ads = self.db.get_ads(admin_id)
        except Exception:
            await query.edit_message_text(
                "❌ حدث خطأ أثناء جلب الإعلانات",
                reply_markup=self._back_keyboard(),
            )
            return

        text, reply_markup = self._build_ads_view(ads)

        if notice:
            text = f"{notice}\n\n{text}"

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
        )

    # ==================================================
    # SHOW ADS
    # ==================================================

    async def show_ads(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await self._send_ads_view(
            update,
            context,
            answer_query=True,
        )

    # ==================================================
    # DELETE AD
    # ==================================================

    async def delete_ad(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        ad_id: int,
    ):
        query = update.callback_query

        if not query:
            return

        await query.answer()

        admin_id = query.from_user.id

        try:
            success = self.db.delete_ad(ad_id, admin_id)
        except Exception:
            success = False

        notice = (
            "✅ تم حذف الإعلان"
            if success
            else "❌ لم يتم العثور على الإعلان أو لا تملك صلاحية حذفه"
        )

        await self._send_ads_view(
            update,
            context,
            notice=notice,
            answer_query=False,
        )

    # ==================================================
    # ADS STATS
    # ==================================================

    async def ad_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        query = update.callback_query

        if not query:
            return

        await query.answer()

        admin_id = query.from_user.id

        try:
            ads = self.db.get_ads(admin_id)
        except Exception:
            await query.edit_message_text(
                "❌ حدث خطأ أثناء جلب إحصائيات الإعلانات",
                reply_markup=self._back_keyboard(),
            )
            return

        count = {
            "text": 0,
            "photo": 0,
            "contact": 0,
        }

        active_count = 0
        inactive_count = 0

        for ad in ads:
            ad_type = self._get_ad_value(ad, "type", 2)
            active = self._get_ad_value(ad, "active", 5, 1)

            if ad_type in count:
                count[ad_type] += 1

            if active == 1:
                active_count += 1
            else:
                inactive_count += 1

        text = (
            "📊 إحصائيات الإعلانات\n\n"
            f"📢 الإجمالي: {len(ads)}\n"
            f"✅ النشطة: {active_count}\n"
            f"⛔ المعطلة: {inactive_count}\n\n"
            f"📝 نصية: {count['text']}\n"
            f"🖼️ صور: {count['photo']}\n"
            f"📞 جهات اتصال: {count['contact']}"
        )

        await query.edit_message_text(
            text,
            reply_markup=self._back_keyboard(),
        )
