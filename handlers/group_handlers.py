from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


class GroupHandlers:
    def __init__(self, db):
        self.db = db

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _back_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_groups")]
        ])

    @staticmethod
    def _get_group_value(group, key: str, index: int, default=None):
        """
        يدعم sqlite3.Row أو tuple/list.
        """
        try:
            return group[key]
        except Exception:
            try:
                return group[index]
            except Exception:
                return default

    @staticmethod
    def _get_status_text(status: str) -> str:
        return {
            "active": "✅ نشطة",
            "inactive": "⛔ معطلة",
            "pending": "⏳ معلقة",
            "joined": "✅ منضمة",
            "failed": "❌ فشل",
        }.get(status, status or "غير معروف")

    def _build_groups_view(self, groups):
        if not groups:
            return (
                "❌ لا توجد مجموعات مضافة",
                self._back_keyboard(),
            )

        text = "👥 المجموعات:\n\n"
        keyboard = []

        for group in groups:
            group_id = self._get_group_value(group, "id", 0)
            link = self._get_group_value(group, "link", 2, "")
            status = self._get_group_value(group, "status", 3, "")
            added_at = self._get_group_value(group, "added_at", 4, "")

            status_text = self._get_status_text(status)

            text += f"#{group_id} — {status_text}\n"

            if link:
                text += f"{link}\n"

            if added_at:
                text += f"📅 {added_at}\n"

            text += "\n"

            keyboard.append([
                InlineKeyboardButton(
                    "🗑 حذف",
                    callback_data=f"delete_group_{group_id}",
                )
            ])

        keyboard.append([
            InlineKeyboardButton("🔙 رجوع", callback_data="back_groups")
        ])

        return text, InlineKeyboardMarkup(keyboard)

    async def _send_groups_view(
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
            groups = self.db.get_groups(admin_id)
        except Exception:
            await query.edit_message_text(
                "❌ حدث خطأ أثناء جلب المجموعات",
                reply_markup=self._back_keyboard(),
            )
            return

        text, reply_markup = self._build_groups_view(groups)

        if notice:
            text = f"{notice}\n\n{text}"

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
        )

    # ==================================================
    # SHOW GROUPS
    # ==================================================

    async def show_groups(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await self._send_groups_view(
            update,
            context,
            answer_query=True,
        )

    # ==================================================
    # DELETE GROUP
    # ==================================================

    async def delete_group(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        group_id: int,
    ):
        query = update.callback_query

        if not query:
            return

        await query.answer()

        admin_id = query.from_user.id

        try:
            success = self.db.delete_group(group_id, admin_id)
        except Exception:
            success = False

        notice = (
            "✅ تم حذف المجموعة"
            if success
            else "❌ لم يتم العثور على المجموعة أو لا تملك صلاحية حذفها"
        )

        await self._send_groups_view(
            update,
            context,
            notice=notice,
            answer_query=False,
        )

    # ==================================================
    # GROUP STATS
    # ==================================================

    async def group_stats(
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
            groups = self.db.get_groups(admin_id)
        except Exception:
            await query.edit_message_text(
                "❌ حدث خطأ أثناء جلب إحصائيات المجموعات",
                reply_markup=self._back_keyboard(),
            )
            return

        total = len(groups)

        active = 0
        inactive = 0
        pending = 0
        joined = 0
        failed = 0
        other = 0

        for group in groups:
            status = self._get_group_value(group, "status", 3, "")

            if status == "active":
                active += 1
            elif status == "inactive":
                inactive += 1
            elif status == "pending":
                pending += 1
            elif status == "joined":
                joined += 1
            elif status == "failed":
                failed += 1
            else:
                other += 1

        text = (
            "📊 إحصائيات المجموعات\n\n"
            f"👥 الإجمالي: {total}\n"
            f"✅ نشطة: {active}\n"
            f"⛔ معطلة: {inactive}\n"
            f"⏳ معلقة: {pending}\n"
            f"✅ منضمة: {joined}\n"
            f"❌ فشل: {failed}\n"
            f"📄 أخرى: {other}"
        )

        await query.edit_message_text(
            text,
            reply_markup=self._back_keyboard(),
        )
