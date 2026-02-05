import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    ADD_PRIVATE_TEXT,
    ADD_GROUP_TEXT,
    ADD_GROUP_PHOTO,
    ADD_RANDOM_REPLY,
    MESSAGES
)

logger = logging.getLogger(__name__)


class ReplyHandlers:

    def __init__(self, db, manager):
        self.db = db
        self.manager = manager

    # ==================================================
    # MAIN MENUS
    # ==================================================

    async def manage_replies(self, query, context):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return

        keyboard = [
            [InlineKeyboardButton("💬 الردود في الخاص", callback_data="private_replies")],
            [InlineKeyboardButton("👥 الردود في القروبات", callback_data="group_replies")],
            [InlineKeyboardButton("🗑️ حذف الردود", callback_data="show_replies")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            "💬 إدارة الردود",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def show_replies_menu(self, query, context):

        keyboard = [
            [InlineKeyboardButton("🗑️ ردود الخاص", callback_data="show_private_replies_delete")],
            [InlineKeyboardButton("🗑️ ردود نصية", callback_data="show_text_replies_delete")],
            [InlineKeyboardButton("🗑️ ردود مع صور", callback_data="show_photo_replies_delete")],
            [InlineKeyboardButton("🗑️ ردود عشوائية", callback_data="show_random_replies_delete")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_replies")]
        ]

        await query.edit_message_text(
            "🗑️ اختر الردود للحذف",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # PRIVATE REPLIES
    # ==================================================

    async def manage_private_replies(self, query, context):

        replies = self.db.get_private_replies(query.from_user.id)

        text = "💬 الردود الخاصة\n\n"

        if replies:
            for r in replies[:10]:
                text += f"#{r[0]} | {r[1][:40]}...\n"
        else:
            text += "❌ لا توجد ردود"

        keyboard = [
            [InlineKeyboardButton("➕ إضافة رد", callback_data="add_private_reply")],
            [InlineKeyboardButton("🚀 بدء الرد", callback_data="start_private_reply")],
            [InlineKeyboardButton("⏹️ إيقاف الرد", callback_data="stop_private_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_replies")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def add_private_reply_start(self, update, context):

        await update.callback_query.edit_message_text(
            "أرسل نص الرد في الخاص الآن:"
        )

        return ADD_PRIVATE_TEXT

    async def add_private_reply_text(self, update, context):

        reply_text = update.message.text.strip()

        if len(reply_text) < 2:
            await update.message.reply_text("❌ النص قصير")
            return ADD_PRIVATE_TEXT

        if self.db.add_private_reply(reply_text, update.message.from_user.id):
            await update.message.reply_text("✅ تم إضافة الرد بنجاح")

        return ConversationHandler.END

    # ==================================================
    # GROUP TEXT REPLY
    # ==================================================

    async def manage_group_replies(self, query, context):

        keyboard = [
            [InlineKeyboardButton("➕ رد نصي", callback_data="add_group_text_reply")],
            [InlineKeyboardButton("➕ رد مع صورة", callback_data="add_group_photo_reply")],
            [InlineKeyboardButton("➕ رد عشوائي", callback_data="add_random_reply")],
            [InlineKeyboardButton("🚀 تشغيل الردود", callback_data="start_group_reply")],
            [InlineKeyboardButton("⏹️ إيقاف الردود", callback_data="stop_group_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_replies")]
        ]

        await query.edit_message_text(
            "👥 إدارة ردود القروبات",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def add_group_text_reply_start(self, update, context):

        await update.callback_query.edit_message_text(
            "أرسل النص المحفز:"
        )

        context.user_data.clear()
        return ADD_GROUP_TEXT

    async def add_group_text_reply_trigger(self, update, context):

        context.user_data['trigger'] = update.message.text.strip()

        await update.message.reply_text(
            "أرسل نص الرد:"
        )

        return ADD_GROUP_TEXT

    async def add_group_text_reply_text(self, update, context):

        trigger = context.user_data.get('trigger')
        reply_text = update.message.text.strip()

        if self.db.add_group_text_reply(trigger, reply_text, update.message.from_user.id):
            await update.message.reply_text("✅ تم إضافة الرد النصي")

        context.user_data.clear()
        return ConversationHandler.END

    # ==================================================
    # GROUP PHOTO REPLY
    # ==================================================

    async def add_group_photo_reply_start(self, update, context):

        await update.callback_query.edit_message_text(
            "أرسل النص المحفز للصورة:"
        )

        context.user_data.clear()
        return ADD_GROUP_PHOTO

    async def add_group_photo_reply_trigger(self, update, context):

        context.user_data['trigger'] = update.message.text.strip()

        await update.message.reply_text(
            "أرسل نص الرد (اختياري):"
        )

        return ADD_GROUP_PHOTO

    async def add_group_photo_reply_text(self, update, context):

        context.user_data['reply_text'] = update.message.text.strip()

        await update.message.reply_text(
            "أرسل الصورة الآن:"
        )

        return ADD_GROUP_PHOTO

    async def add_group_photo_reply_photo(self, update, context):

        trigger = context.user_data.get('trigger')
        reply_text = context.user_data.get('reply_text', '')

        os.makedirs("temp_files/group_replies", exist_ok=True)

        photo = update.message.photo[-1]
        file = await photo.get_file()

        path = f"temp_files/group_replies/{datetime.now().timestamp()}.jpg"
        await file.download_to_drive(path)

        if self.db.add_group_photo_reply(trigger, reply_text, path, update.message.from_user.id):
            await update.message.reply_text("✅ تم إضافة الرد مع الصورة")

        context.user_data.clear()
        return ConversationHandler.END

    # ==================================================
    # RANDOM REPLY
    # ==================================================

    async def add_random_reply_start(self, update, context):

        await update.callback_query.edit_message_text(
            "أرسل نص الرد العشوائي:"
        )

        context.user_data.clear()
        return ADD_RANDOM_REPLY

    async def add_random_reply_text(self, update, context):

        context.user_data['random_text'] = update.message.text.strip()

        await update.message.reply_text(
            "أرسل صورة أو /skip للتخطي"
        )

        return ADD_RANDOM_REPLY

    async def add_random_reply_media(self, update, context):

        text = context.user_data['random_text']

        media_path = None

        if update.message.photo:
            os.makedirs("temp_files/random_replies", exist_ok=True)
            file = await update.message.photo[-1].get_file()
            media_path = f"temp_files/random_replies/{datetime.now().timestamp()}.jpg"
            await file.download_to_drive(media_path)

        self.db.add_group_random_reply(text, media_path, update.message.from_user.id)

        await update.message.reply_text("✅ تم إضافة الرد العشوائي")

        context.user_data.clear()
        return ConversationHandler.END

    async def skip_random_reply_media(self, update, context):

        text = context.user_data['random_text']

        self.db.add_group_random_reply(text, None, update.message.from_user.id)

        await update.message.reply_text("✅ تم إضافة الرد بدون صورة")

        context.user_data.clear()
        return ConversationHandler.END

    # ==================================================
    # START / STOP SYSTEMS
    # ==================================================

    async def start_private_reply(self, query, context):

        if self.manager.start_private_reply(query.from_user.id):
            await query.edit_message_text("✅ تم تشغيل الرد الخاص")
        else:
            await query.edit_message_text("⚠️ يعمل بالفعل")

    async def stop_private_reply(self, query, context):

        if self.manager.stop_private_reply(query.from_user.id):
            await query.edit_message_text("⏹️ تم الإيقاف")
        else:
            await query.edit_message_text("⚠️ غير نشط")

    async def start_group_reply(self, query, context):

        if self.manager.start_group_reply(query.from_user.id):
            await query.edit_message_text("✅ تم تشغيل الردود الجماعية")
        else:
            await query.edit_message_text("⚠️ تعمل بالفعل")

    async def stop_group_reply(self, query, context):

        if self.manager.stop_group_reply(query.from_user.id):
            await query.edit_message_text("⏹️ تم الإيقاف")
        else:
            await query.edit_message_text("⚠️ غير نشط")

    async def start_random_reply(self, query, context):

        if self.manager.start_random_reply(query.from_user.id):
            await query.edit_message_text("🎲 تم تشغيل الرد العشوائي")
        else:
            await query.edit_message_text("⚠️ يعمل بالفعل")

    async def stop_random_reply(self, query, context):

        if self.manager.stop_random_reply(query.from_user.id):
            await query.edit_message_text("⏹️ تم الإيقاف")
        else:
            await query.edit_message_text("⚠️ غير نشط")
