from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


class AccountHandlers:
    def __init__(self, db):
        self.db = db

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _get_account_value(account, key: str, index: int, default=None):
        """
        يدعم sqlite3.Row أو tuple/list.
        """
        try:
            return account[key]
        except Exception:
            try:
                return account[index]
            except Exception:
                return default

    @staticmethod
    def _back_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_accounts")]
        ])

    def _build_accounts_view(self, accounts):
        """
        تجهيز النص والأزرار لقائمة الحسابات.
        """
        if not accounts:
            return (
                "❌ لا توجد حسابات مضافة",
                self._back_keyboard()
            )

        text = "👥 الحسابات:\n\n"
        keyboard = []

        for account in accounts:
            acc_id = self._get_account_value(account, "id", 0)
            active = self._get_account_value(account, "active", 3, 0)
            added_at = self._get_account_value(account, "added_at", 4, "")

            status = "✅ نشط" if active == 1 else "⛔ معطل"

            text += f"#{acc_id} — {status}\n"
            text += f"📅 {added_at}\n\n"

            keyboard.append([
                InlineKeyboardButton(
                    "🔁 تفعيل / تعطيل",
                    callback_data=f"toggle_account_{acc_id}",
                ),
                InlineKeyboardButton(
                    "🗑 حذف",
                    callback_data=f"delete_account_{acc_id}",
                ),
            ])

        keyboard.append([
            InlineKeyboardButton("🔙 رجوع", callback_data="back_accounts")
        ])

        return text, InlineKeyboardMarkup(keyboard)

    async def _send_accounts_view(
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
            accounts = self.db.get_accounts(admin_id)
        except Exception:
            await query.edit_message_text(
                "❌ حدث خطأ أثناء جلب الحسابات",
                reply_markup=self._back_keyboard(),
            )
            return

        text, reply_markup = self._build_accounts_view(accounts)

        if notice:
            text = f"{notice}\n\n{text}"

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
        )

    # ==================================================
    # SHOW ACCOUNTS
    # ==================================================

    async def show_accounts(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        await self._send_accounts_view(
            update,
            context,
            answer_query=True,
        )

    # ==================================================
    # TOGGLE ACCOUNT
    # ==================================================

    async def toggle_account(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        account_id: int,
    ):
        query = update.callback_query

        if not query:
            return

        await query.answer()

        admin_id = query.from_user.id

        try:
            success = self.db.toggle_account_status(account_id, admin_id)
        except Exception:
            success = False

        notice = (
            "✅ تم تحديث حالة الحساب"
            if success
            else "❌ لم يتم العثور على الحساب أو لا تملك صلاحية تعديله"
        )

        await self._send_accounts_view(
            update,
            context,
            notice=notice,
            answer_query=False,
        )

    # ==================================================
    # DELETE ACCOUNT
    # ==================================================

    async def delete_account(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        account_id: int,
    ):
        query = update.callback_query

        if not query:
            return

        await query.answer()

        admin_id = query.from_user.id

        try:
            success = self.db.delete_account(account_id, admin_id)
        except Exception:
            success = False

        notice = (
            "✅ تم حذف الحساب"
            if success
            else "❌ لم يتم العثور على الحساب أو لا تملك صلاحية حذفه"
        )

        await self._send_accounts_view(
            update,
            context,
            notice=notice,
            answer_query=False,
        )
