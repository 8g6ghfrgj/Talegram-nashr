from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


class ReplyHandlers:
    def __init__(self, db):
        self.db = db

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _back_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
        ])

    @staticmethod
    def _get_reply_value(reply, key: str, index: int, default=None):
        """
        يدعم sqlite3.Row أو tuple/list.
        """
        try:
            return reply[key]
        except Exception:
            try:
                return reply[index]
            except Exception:
                return default

    @staticmethod
    def _short_text(text: Optional[str], limit: int = 40) -> str:
        if not text:
            return "بدون نص"

        text = text.strip()

        if len(text) <= limit:
            return text

        return text[:limit] + "..."

    def _build_replies_view(self, private_replies, random_replies):
        if not private_replies and not random_replies:
            return (
                "❌ لا توجد ردود مضافة",
                self._back_keyboard(),
            )

        text = "💬 الردود:\n\n"
        keyboard = []

        # ---------- PRIVATE ----------
        if private_replies:
            text += "🔒 الردود الخاصة:\n"

            for reply in private_replies:
                reply_id = self._get_reply_value(reply, "id", 0)
                reply_text = self._get_reply_value(reply, "text", 2, "")
                added_at = self._get_reply_value(reply, "added_at", 3, "")

                text += f"#{reply_id} — {self._short_text(reply_text)}\n"

                if added_at:
                    text += f"📅 {added_at}\n"

                text += "\n"

                keyboard.append([
                    InlineKeyboardButton(
                        "🗑 حذف (خاص)",
                        callback_data=f"delete_private_reply_{reply_id}",
                    )
                ])

        # ---------- RANDOM ----------
        if random_replies:
            text += "🎲 الردود العشوائية:\n"

            for reply in random_replies:
                reply_id = self._get_reply_value(reply, "id", 0)
                reply_type = self._get_reply_value(reply, "type", 2, "unknown")
                reply_text = self._get_reply_value(reply, "text", 3, "")
                media_path = self._get_reply_value(reply, "media_path", 4, None)
                added_at = self._get_reply_value(reply, "added_at", 5, "")

                desc = self._short_text(reply_text, limit=30)
                media = "🖼️ صورة" if media_path else "بدون صورة"

                text += f"#{reply_id} — {reply_type} | {desc} | {media}\n"

                if added_at:
                    text += f"📅 {added_at}\n"

                text += "\n"

                keyboard.append([
                    InlineKeyboardButton(
                        "🗑 حذف (عشوائي)",
                        callback_data=f"delete_random_reply_{reply_id}",
                    )
                ])

        keyboard.append([
            InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")
        ])

        return text, InlineKeyboardMarkup(keyboard)

    async def _send_replies_view(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        notice: Optional[str] = None,
        answer_query: bool = True,
    ):
        query = update.callback_query

        if not query:
            return

        if answer_query:
            await query.answer()

        admin_id = query.from_user.id

        try:
            private_replies = self.db.get_private_replies(admin_id)
            random_replies = self.db.get_random_replies(admin_id)
        except Exception:
            await query.edit_message_text(
                "❌ حدث خطأ أثناء جلب الردود",
                reply_markup=self._back_keyboard(),
            )
            return

        text, reply_markup = self._build_replies_view(
            private_replies,
            random_replies,
        )

        if notice:
            text = f"{notice}\n\n{text}"

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
        )

    # ==================================================
    # SHOW ALL REPLIES
    # ==================================================

    async def show_replies(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await self._send_replies_view(
            update,
            context,
            answer_query=True,
        )

    # ==================================================
    # DELETE PRIVATE REPLY
    # ==================================================

    async def delete_private_reply(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        reply_id: int,
    ):
        query = update.callback_query

        if not query:
            return

        await query.answer()

        admin_id = query.from_user.id

        try:
            success = self.db.delete_private_reply(reply_id, admin_id)
        except Exception:
            success = False

        notice = (
            "✅ تم حذف الرد الخاص"
            if success
            else "❌ لم يتم العثور على الرد أو لا تملك صلاحية حذفه"
        )

        await self._send_replies_view(
            update,
            context,
            notice=notice,
            answer_query=False,
        )

    # ==================================================
    # DELETE RANDOM REPLY
    # ==================================================

    async def delete_random_reply(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        reply_id: int,
    ):
        query = update.callback_query

        if not query:
            return

        await query.answer()

        admin_id = query.from_user.id

        try:
            success = self.db.delete_random_reply(reply_id, admin_id)
        except Exception:
            success = False

        notice = (
            "✅ تم حذف الرد العشوائي"
            if success
            else "❌ لم يتم العثور على الرد أو لا تملك صلاحية حذفه"
        )

        await self._send_replies_view(
            update,
            context,
            notice=notice,
            answer_query=False,
        )
