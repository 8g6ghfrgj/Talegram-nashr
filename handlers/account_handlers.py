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
    # MAIN MENU
    # ==================================================

    async def manage_accounts(self, query, context):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        keyboard = [
            [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")],
            [InlineKeyboardButton("👥 عرض الحسابات", callback_data="show_accounts")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="account_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            "👥 إدارة الحسابات",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # ADD ACCOUNT
    # ==================================================

    async def add_account_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not self.db.is_admin(update.callback_query.from_user.id):
            await update.callback_query.edit_message_text(MESSAGES["unauthorized"])
            return ConversationHandler.END

        await update.callback_query.edit_message_text(
            "أرسل Session String للحساب:"
        )

        return ADD_ACCOUNT

    async def add_account_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not self.db.is_admin(update.message.from_user.id):
            await update.message.reply_text(MESSAGES["unauthorized"])
            return ConversationHandler.END

        session_string = update.message.text.strip()

        if len(session_string) < 100:
            await update.message.reply_text("❌ كود الجلسة غير صحيح")
            return ADD_ACCOUNT

        await update.message.reply_text("⏳ جاري اختبار الجلسة...")

        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession

            client = TelegramClient(StringSession(session_string), 1, "b")
            await client.connect()

            if not await client.is_user_authorized():
                await client.disconnect()
                await update.message.reply_text("❌ الجلسة غير صالحة")
                return ADD_ACCOUNT

            me = await client.get_me()
            await client.disconnect()

            phone = me.phone or "غير معروف"
            name = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
            username = f"@{me.username}" if me.username else "لا يوجد"

            success, message = self.db.add_account(
                session_string,
                phone,
                name,
                username,
                update.message.from_user.id
            )

            if success:
                keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_accounts")]]

                await update.message.reply_text(
                    f"✅ {message}\n\n"
                    f"الاسم: {name}\n"
                    f"الهاتف: {phone}\n"
                    f"المستخدم: {username}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(f"❌ {message}")

            return ConversationHandler.END

        except Exception as e:
            logger.error(e)
            await update.message.reply_text("❌ خطأ في الجلسة")
            return ADD_ACCOUNT

    # ==================================================
    # SHOW ACCOUNTS
    # ==================================================

    async def show_accounts(self, query, context):

        accounts = self.db.get_accounts(query.from_user.id)

        if not accounts:
            await query.edit_message_text("❌ لا توجد حسابات")
            return

        stats = self.db.get_statistics(query.from_user.id)

        text = f"👥 الحسابات ({stats['accounts']['active']}/{stats['accounts']['total']} نشطة)\n\n"
        keyboard = []

        for acc in accounts[:20]:

            acc_id, session, phone, name, username, is_active, added, status, last_pub = acc

            emoji = "🟢" if is_active else "🔴"

            text += (
                f"#{acc_id} - {name}\n"
                f"{emoji} {phone}\n"
                f"{username}\n"
            )

            if last_pub:
                text += f"آخر نشر: {last_pub[:16]}\n"

            text += "────────────\n"

            keyboard.append([
                InlineKeyboardButton(f"🗑️ حذف #{acc_id}", callback_data=f"delete_account_{acc_id}"),
                InlineKeyboardButton(
                    "⏸️ إيقاف" if is_active else "▶️ تشغيل",
                    callback_data=f"toggle_account_{acc_id}"
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

    async def delete_account(self, query, context, account_id):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        if self.db.delete_account(account_id, query.from_user.id):
            await query.edit_message_text("✅ تم حذف الحساب")
        else:
            await query.edit_message_text("❌ فشل حذف الحساب")

        await self.show_accounts(query, context)

    # ==================================================
    # TOGGLE ACCOUNT
    # ==================================================

    async def toggle_account_status(self, query, context, account_id):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        if self.db.toggle_account_status(account_id, query.from_user.id):
            await query.edit_message_text("✅ تم تغيير حالة الحساب")
        else:
            await query.edit_message_text("❌ فشل تغيير الحالة")

        await self.show_accounts(query, context)

    # ==================================================
    # STATS
    # ==================================================

    async def show_account_stats(self, query, context):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        stats = self.db.get_statistics(query.from_user.id)

        text = (
            "📊 إحصائيات الحسابات\n\n"
            f"الإجمالي: {stats['accounts']['total']}\n"
            f"النشطة: {stats['accounts']['active']}\n"
            f"غير النشطة: {stats['accounts']['total'] - stats['accounts']['active']}\n\n"
            f"الإعلانات: {stats['ads']}\n"
            f"المجموعات: {stats['groups']['total']}"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="account_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_accounts")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
