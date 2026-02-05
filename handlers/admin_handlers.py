import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADD_ADMIN, OWNER_ID, MESSAGES

logger = logging.getLogger(__name__)


class AdminHandlers:

    def __init__(self, db, manager):
        self.db = db
        self.manager = manager

    # ==================================================
    # HELPERS
    # ==================================================

    def is_owner(self, user_id: int) -> bool:
        return user_id == OWNER_ID

    # ==================================================
    # MAIN MENU
    # ==================================================

    async def manage_admins(self, query, context):

        if not self.is_owner(query.from_user.id):
            await query.edit_message_text(
                MESSAGES["owner_only"].format(OWNER_ID)
            )
            return

        keyboard = [
            [InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")],
            [InlineKeyboardButton("👨‍💼 عرض المشرفين", callback_data="show_admins")],
            [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            f"👨‍💼 إدارة المشرفين\n\n👑 المالك: {OWNER_ID}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # ADD ADMIN
    # ==================================================

    async def add_admin_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not self.is_owner(update.callback_query.from_user.id):
            await update.callback_query.edit_message_text(
                MESSAGES["owner_only"].format(OWNER_ID)
            )
            return ConversationHandler.END

        await update.callback_query.edit_message_text(
            "📩 أرسل User ID للمشرف الجديد:"
        )

        return ADD_ADMIN

    async def add_admin_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not self.is_owner(update.message.from_user.id):
            await update.message.reply_text(
                MESSAGES["owner_only"].format(OWNER_ID)
            )
            return ConversationHandler.END

        try:
            admin_user_id = int(update.message.text.strip())

            if admin_user_id <= 0 or admin_user_id == OWNER_ID:
                await update.message.reply_text("❌ معرف غير صالح")
                return ADD_ADMIN

            try:
                user = await context.bot.get_chat(admin_user_id)
                username = f"@{user.username}" if user.username else "لا يوجد"
                full_name = (
                    f"{user.first_name} {user.last_name}"
                    if user.last_name else user.first_name
                )
            except Exception:
                username = "غير معروف"
                full_name = f"مستخدم {admin_user_id}"

            success, message = self.db.add_admin(
                admin_user_id,
                username,
                full_name,
                False
            )

            keyboard = [
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")]
            ]

            await update.message.reply_text(
                f"{'✅' if success else '❌'} {message}\n\n"
                f"👤 الاسم: {full_name}\n"
                f"🆔 المعرف: {admin_user_id}\n"
                f"🔗 المستخدم: {username}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            return ADD_ADMIN

    # ==================================================
    # SHOW ADMINS
    # ==================================================

    async def show_admins(self, query, context):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        admins = self.db.get_admins()

        if not admins:
            await query.edit_message_text("❌ لا يوجد مشرفون")
            return

        text = "👨‍💼 قائمة المشرفين\n\n"
        keyboard = []

        can_delete = self.is_owner(query.from_user.id)

        for admin in admins:

            admin_id, user_id, username, full_name, added_date, is_super = admin

            if user_id == OWNER_ID:
                role = "👑 المالك"
            elif is_super:
                role = "🟢 رئيسي"
            else:
                role = "🔵 عادي"

            text += (
                f"#{admin_id} - {full_name}\n"
                f"ID: {user_id}\n"
                f"{username}\n"
                f"الدور: {role}\n"
                "────────────\n"
            )

            if can_delete and user_id != OWNER_ID:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗑️ حذف #{admin_id}",
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

    async def delete_admin(self, query, context, admin_id):

        if not self.is_owner(query.from_user.id):
            await query.edit_message_text(
                MESSAGES["owner_only"].format(OWNER_ID)
            )
            return

        if self.db.delete_admin(admin_id):
            await query.edit_message_text(f"✅ تم حذف المشرف #{admin_id}")
        else:
            await query.edit_message_text("❌ فشل حذف المشرف")

        await self.show_admins(query, context)

    # ==================================================
    # SYSTEM STATS
    # ==================================================

    async def show_system_stats(self, query, context):

        if not self.is_owner(query.from_user.id):
            await query.edit_message_text(
                MESSAGES["owner_only"].format(OWNER_ID)
            )
            return

        stats = self.db.get_statistics()

        text = (
            "📊 إحصائيات النظام\n\n"
            f"👥 الحسابات: {stats['accounts']['total']} "
            f"(نشطة {stats['accounts']['active']})\n\n"
            f"📢 الإعلانات: {stats['ads']}\n\n"
            f"👥 المجموعات: {stats['groups']['total']}\n"
            f"✅ المنضمة: {stats['groups']['joined']}\n"
            f"⏳ المعلقة: {stats['groups']['total'] - stats['groups']['joined']}\n"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
