import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import ADD_ACCOUNT, MESSAGES

logger = logging.getLogger(__name__)


class AccountHandlers:

    def __init__(self, db, manager):
        self.db = db
        self.manager = manager


    # ==================================================
    # ACCOUNTS MENU
    # ==================================================

    async def manage_accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        keyboard = [
            [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")],
            [InlineKeyboardButton("📋 عرض الحسابات", callback_data="show_accounts")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="account_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            "👥 إدارة الحسابات",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # START ADD ACCOUNT
    # ==================================================

    async def add_account_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return ConversationHandler.END

        context.user_data.clear()

        keyboard = [
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_process")]
        ]

        await query.edit_message_text(
            "📥 أرسل جلسة الحساب الآن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ADD_ACCOUNT


    # ==================================================
    # ADD ACCOUNT SESSION
    # ==================================================

    async def add_account_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        message = update.message
        user_id = message.from_user.id

        session_data = message.text.strip()

        if len(session_data) < 5:
            await message.reply_text("❌ الجلسة غير صالحة")
            return ADD_ACCOUNT

        success, msg = self.db.add_account(user_id, session_data)

        if success:
            await message.reply_text("✅ تم إضافة الحساب بنجاح")
        else:
            await message.reply_text(f"❌ {msg}")

        context.user_data.clear()
        return ConversationHandler.END


    # ==================================================
    # SHOW ACCOUNTS
    # ==================================================

    async def show_accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        accounts = self.db.get_accounts(user_id)

        if not accounts:
            await query.edit_message_text("❌ لا توجد حسابات")
            return

        text = "👥 الحسابات المسجلة:\n\n"
        keyboard = []

        for acc in accounts[:15]:

            # DB schema:
            # id, admin_id, session, active, added
            acc_id, admin_id, session, status, added = acc

            status_icon = "✅" if status == 1 else "⛔"

            text += f"#{acc_id} {status_icon}\n"
            text += f"{session[:40]}...\n"
            text += f"{added}\n──────────\n"

            keyboard.append([
                InlineKeyboardButton(
                    f"{'⛔ تعطيل' if status == 1 else '✅ تفعيل'}",
                    callback_data=f"toggle_account_{acc_id}"
                ),
                InlineKeyboardButton(
                    "🗑 حذف",
                    callback_data=f"delete_account_{acc_id}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton("🔄 تحديث", callback_data="show_accounts"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_accounts")
        ])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # DELETE ACCOUNT
    # ==================================================

    async def delete_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE, account_id: int):

        query = update.callback_query
        user_id = query.from_user.id

        if self.db.delete_account(account_id, user_id):
            await query.answer("✅ تم حذف الحساب")
        else:
            await query.answer("❌ فشل الحذف")

        await self.show_accounts(update, context)


    # ==================================================
    # TOGGLE ACCOUNT STATUS
    # ==================================================

    async def toggle_account_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, account_id: int):

        query = update.callback_query
        user_id = query.from_user.id

        if self.db.toggle_account_status(account_id, user_id):
            await query.answer("🔁 تم تغيير الحالة")
        else:
            await query.answer("❌ فشل التغيير")

        await self.show_accounts(update, context)


    # ==================================================
    # ACCOUNT STATS
    # ==================================================

    async def show_account_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        accounts = self.db.get_accounts(user_id)

        total = len(accounts)
        active = len([a for a in accounts if a[3] == 1])
        inactive = total - active

        text = (
            "📊 إحصائيات الحسابات\n\n"
            f"👥 الإجمالي: {total}\n"
            f"✅ النشطة: {active}\n"
            f"⛔ المعطلة: {inactive}"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="account_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_accounts")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
