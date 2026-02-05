import logging
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADD_GROUP, MESSAGES, DELAY_SETTINGS

logger = logging.getLogger(__name__)


class GroupHandlers:

    def __init__(self, db, manager):
        self.db = db
        self.manager = manager

    # ==================================================
    # MAIN MENU
    # ==================================================

    async def manage_groups(self, query, context):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        keyboard = [
            [InlineKeyboardButton("➕ إضافة مجموعة", callback_data="add_group")],
            [InlineKeyboardButton("👥 عرض المجموعات", callback_data="show_groups")],
            [InlineKeyboardButton("🚀 بدء الانضمام", callback_data="start_join_groups")],
            [InlineKeyboardButton("⏹️ إيقاف الانضمام", callback_data="stop_join_groups")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="group_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            "👥 إدارة المجموعات",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # ADD GROUPS
    # ==================================================

    async def add_group_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        await update.callback_query.edit_message_text(
            "أرسل روابط المجموعات الآن (رابط واحد أو عدة روابط):"
        )

        return ADD_GROUP

    async def add_group_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        text = update.message.text

        links = re.findall(r'(https?://t\.me/[^\s]+|t\.me/[^\s]+|\+[a-zA-Z0-9_\-]+|@[a-zA-Z0-9_]+)', text)

        if not links:
            await update.message.reply_text("❌ لم يتم العثور على روابط صحيحة")
            return ADD_GROUP

        added = 0
        invalid = []

        for link in links:

            clean = link.strip()

            if not self.is_valid_telegram_link(clean):
                invalid.append(clean)
                continue

            if self.db.add_group(clean, update.message.from_user.id):
                added += 1

        response = f"✅ تمت العملية\n\nالمضافة: {added}\nغير الصالحة: {len(invalid)}"

        if added:
            asyncio.create_task(self.delayed_join_groups(update.message.from_user.id))

        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]]

        await update.message.reply_text(
            response,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ConversationHandler.END

    # ==================================================
    # LINK VALIDATION
    # ==================================================

    def is_valid_telegram_link(self, link):

        patterns = [
            r'^https?://t\.me/[a-zA-Z0-9_]+$',
            r'^https?://t\.me/\+[a-zA-Z0-9_\-]+$',
            r'^https?://t\.me/addlist/[a-zA-Z0-9_\-]+$',
            r'^t\.me/[a-zA-Z0-9_]+$',
            r'^t\.me/\+[a-zA-Z0-9_\-]+$',
            r'^t\.me/addlist/[a-zA-Z0-9_\-]+$',
            r'^\+[a-zA-Z0-9_\-]+$',
            r'^@[a-zA-Z0-9_]+$'
        ]

        return any(re.match(p, link) for p in patterns)

    # ==================================================
    # AUTO JOIN
    # ==================================================

    async def delayed_join_groups(self, admin_id):

        await asyncio.sleep(2)

        accounts = self.db.get_active_publishing_accounts(admin_id)
        groups = self.db.get_groups(admin_id, status="pending")

        if not accounts or not groups:
            return

        self.manager.start_join_groups(admin_id)

    # ==================================================
    # SHOW GROUPS
    # ==================================================

    async def show_groups(self, query, context):

        groups = self.db.get_groups(query.from_user.id)

        if not groups:
            await query.edit_message_text("❌ لا توجد مجموعات")
            return

        pending = sum(1 for g in groups if g[2] == "pending")
        joined = sum(1 for g in groups if g[2] == "joined")
        failed = sum(1 for g in groups if g[2] == "failed")

        text = f"👥 المجموعات\n⏳ {pending} | ✅ {joined} | ❌ {failed}\n\n"

        keyboard = []

        for g in groups[:15]:

            gid, link, status, join_date, added_date, admin_id, last_checked = g

            emoji = {"pending": "⏳", "joined": "✅", "failed": "❌"}.get(status, "❓")

            text += f"#{gid} - {link}\n{emoji} {status}\n"
            text += "────────────\n"

            keyboard.append([
                InlineKeyboardButton(f"🗑️ حذف #{gid}", callback_data=f"delete_group_{gid}")
            ])

        keyboard.append([
            InlineKeyboardButton("🔄 تحديث", callback_data="show_groups"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")
        ])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # DELETE GROUP
    # ==================================================

    async def delete_group(self, query, context, group_id):

        if self.db.delete_group(group_id, query.from_user.id):
            await query.edit_message_text(f"✅ تم حذف المجموعة #{group_id}")
        else:
            await query.edit_message_text("❌ فشل حذف المجموعة")

        await self.show_groups(query, context)

    # ==================================================
    # START / STOP JOIN
    # ==================================================

    async def start_join_groups(self, query, context):

        admin_id = query.from_user.id

        accounts = self.db.get_active_publishing_accounts(admin_id)
        groups = self.db.get_groups(admin_id, status="pending")

        if not accounts:
            await query.edit_message_text("❌ لا توجد حسابات نشطة")
            return

        if not groups:
            await query.edit_message_text("❌ لا توجد مجموعات معلقة")
            return

        if self.manager.start_join_groups(admin_id):

            await query.edit_message_text(
                f"🚀 بدأ الانضمام\n\n"
                f"الحسابات: {len(accounts)}\n"
                f"المجموعات: {len(groups)}\n"
                f"التأخير: {DELAY_SETTINGS['join_groups']['between_links']} ثانية"
            )
        else:
            await query.edit_message_text("⚠️ الانضمام يعمل بالفعل")

    async def stop_join_groups(self, query, context):

        if self.manager.stop_join_groups(query.from_user.id):
            await query.edit_message_text("⏹️ تم الإيقاف")
        else:
            await query.edit_message_text("⚠️ غير نشط")

    # ==================================================
    # STATS
    # ==================================================

    async def show_group_stats(self, query, context):

        stats = self.db.get_statistics(query.from_user.id)

        text = (
            "📊 إحصائيات المجموعات\n\n"
            f"الإجمالي: {stats['groups']['total']}\n"
            f"المنضمة: {stats['groups']['joined']}\n"
            f"المعلقة: {stats['groups']['total'] - stats['groups']['joined']}\n\n"
            f"بين الروابط: {DELAY_SETTINGS['join_groups']['between_links']} ثانية\n"
            f"بين الدورات: {DELAY_SETTINGS['join_groups']['between_cycles']} ثانية"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="group_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
