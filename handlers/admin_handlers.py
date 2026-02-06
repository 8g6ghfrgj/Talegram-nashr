import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import ADD_ADMIN, MESSAGES

logger = logging.getLogger(__name__)


class AdminHandlers:

    def __init__(self, db, manager):
        self.db = db
        self.manager = manager


    # ==================================================
    # ADMINS MENU
    # ==================================================

    async def manage_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        keyboard = [
            [InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")],
            [InlineKeyboardButton("📋 عرض المشرفين", callback_data="show_admins")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            "👨‍💼 إدارة المشرفين",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # START ADD ADMIN
    # ==================================================

    async def add_admin_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return ConversationHandler.END

        context.user_data.clear()

        await query.edit_message_text(
            "🆔 أرسل ID المستخدم لإضافته كمشرف:"
        )

        return ADD_ADMIN


    # ==================================================
    # ADD ADMIN ID
    # ==================================================

    async def add_admin_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        message = update.message
        user_id = message.from_user.id

        try:
            new_admin_id = int(message.text.strip())
        except ValueError:
            await message.reply_text("❌ الرجاء إرسال ID رقمي صحيح")
            return ADD_ADMIN

        success, msg = self.db.add_admin(
            new_admin_id,
            f"admin_{new_admin_id}",
            "مشرف",
            True
        )

        if success:
            await message.reply_text("✅ تم إضافة المشرف بنجاح")
        else:
            await message.reply_text(f"❌ {msg}")

        context.user_data.clear()
        return ConversationHandler.END


    # ==================================================
    # SHOW ADMINS
    # ==================================================

    async def show_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        user_id = query.from_user.id

        admins = self.db.get_admins()

        if not admins:
            await query.edit_message_text("❌ لا يوجد مشرفين")
            return

        text = "👨‍💼 قائمة المشرفين\n\n"
        keyboard = []

        for admin in admins[:15]:

            admin_id, username, role, status, added = admin

            status_icon = "✅" if status else "⛔"

            text += f"#{admin_id} {status_icon}\n"
            text += f"{username} - {role}\n"
            text += f"{added[:16]}\n──────────\n"

            keyboard.append([
                InlineKeyboardButton(
                    f"{'⛔ تعطيل' if status else '✅ تفعيل'} #{admin_id}",
                    callback_data=f"toggle_admin_{admin_id}"
                ),
                InlineKeyboardButton(
                    f"🗑 حذف #{admin_id}",
                    callback_data=f"delete_admin_{admin_id}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton("🔄 تحديث", callback_data="show_admins"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")
        ])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # DELETE ADMIN
    # ==================================================

    async def delete_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int):

        query = update.callback_query

        if self.db.delete_admin(admin_id):
            await query.answer("✅ تم الحذف")
        else:
            await query.answer("❌ فشل الحذف")

        await self.show_admins(update, context)


    # ==================================================
    # TOGGLE ADMIN STATUS
    # ==================================================

    async def toggle_admin_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int):

        query = update.callback_query

        if self.db.toggle_admin_status(admin_id):
            await query.answer("🔁 تم التغيير")
        else:
            await query.answer("❌ فشل التغيير")

        await self.show_admins(update, context)


    # ==================================================
    # SYSTEM STATS
    # ==================================================

    async def show_system_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query

        stats = self.db.get_system_statistics()

        text = (
            "📊 إحصائيات النظام\n\n"
            f"👨‍💼 المشرفين: {stats.get('admins', 0)}\n"
            f"👥 الحسابات: {stats.get('accounts', 0)}\n"
            f"📢 الإعلانات: {stats.get('ads', 0)}\n"
            f"👥 المجموعات: {stats.get('groups', 0)}\n"
            f"💬 الردود: {stats.get('replies', 0)}"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
