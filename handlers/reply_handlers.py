import logging
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
    # MAIN MENU
    # ==================================================

    async def manage_replies(self, query, context):

        if not self.db.is_admin(query.from_user.id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return

        keyboard = [
            [InlineKeyboardButton("💬 الردود في الخاص", callback_data="private_replies")],
            [InlineKeyboardButton("👥 الردود في القروبات", callback_data="group_replies")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            "💬 إدارة الردود",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # PRIVATE REPLIES
    # ==================================================

    async def manage_private_replies(self, query, context):

        replies = self.db.get_private_replies(query.from_user.id)

        text = "💬 ردود الخاص\n\n"

        if replies:
            for r in replies[:10]:
                text += f"#{r[0]} | {r[1][:40]}...\n"
        else:
            text += "❌ لا توجد ردود"

        keyboard = [
            [InlineKeyboardButton("➕ إضافة رد", callback_data="add_private_reply")],
            [InlineKeyboardButton("🚀 تشغيل", callback_data="start_private_reply")],
            [InlineKeyboardButton("⏹️ إيقاف", callback_data="stop_private_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_replies")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def add_private_reply_start(self, update, context):

        await update.callback_query.edit_message_text(
            "✍️ أرسل نص الرد في الخاص:"
        )

        return ADD_PRIVATE_TEXT

    async def add_private_reply_text(self, update, context):

        text = update.message.text.strip()

        if len(text) < 2:
            await update.message.reply_text("❌ النص قصير")
            return ADD_PRIVATE_TEXT

        self.db.add_private_reply(text, update.message.from_user.id)

        await update.message.reply_text("✅ تم حفظ الرد")

        return ConversationHandler.END

    # ==================================================
    # GROUP REPLIES MENU
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
            "👥 ردود القروبات",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================================
    # GROUP TEXT REPLY (TRIGGER -> TEXT)
    # ==================================================

    async def add_group_text_reply_start(self, update, context):

        context.user_data.clear()

        await update.callback_query.edit_message_text(
            "🧩 أرسل الكلمة المحفزة:"
        )

        return ADD_GROUP_TEXT

    async def add_group_text_reply_trigger(self, update, context):

        context.user_data["trigger"] = update.message.text.strip()

        await update.message.reply_text(
            "✍️ أرسل نص الرد:"
        )

        return ADD_GROUP_TEXT

    async def add_group_text_reply_text(self, update, context):

        trigger = context.user_data.get("trigger")
        reply_text = update.message.text.strip()

        if not trigger:
            await update.message.reply_text("❌ لم يتم تحديد المحفز")
            return ConversationHandler.END

        self.db.add_group_text_reply(
            trigger,
            reply_text,
            update.message.from_user.id
        )

        await update.message.reply_text("✅ تم إضافة الرد النصي")

        context.user_data.clear()
        return ConversationHandler.END

    # ==================================================
    # GROUP PHOTO REPLY
    # ==================================================

    async def add_group_photo_reply_start(self, update, context):

        context.user_data.clear()

        await update.callback_query.edit_message_text(
            "🧩 أرسل الكلمة المحفزة للصورة:"
        )

        return ADD_GROUP_PHOTO

    async def add_group_photo_reply_trigger(self, update, context):

        context.user_data["trigger"] = update.message.text.strip()

        await update.message.reply_text(
            "✍️ أرسل نص الرد (اختياري):"
        )

        return ADD_GROUP_PHOTO

    async def add_group_photo_reply_text(self, update, context):

        context.user_data["reply_text"] = update.message.text.strip()

        await update.message.reply_text(
            "🖼️ أرسل الصورة:"
        )

        return ADD_GROUP_PHOTO

    async def add_group_photo_reply_photo(self, update, context):

        trigger = context.user_data.get("trigger")
        reply_text = context.user_data.get("reply_text", "")

        if not trigger:
            await update.message.reply_text("❌ لم يتم تحديد المحفز")
            return ConversationHandler.END

        os.makedirs("temp_files/group_replies", exist_ok=True)

        file = await update.message.photo[-1].get_file()
        path = f"temp_files/group_replies/{int(datetime.now().timestamp())}.jpg"

        await file.download_to_drive(path)

        self.db.add_group_photo_reply(
            trigger,
            reply_text,
            path,
            update.message.from_user.id
        )

        await update.message.reply_text("✅ تم إضافة الرد مع الصورة")

        context.user_data.clear()
        return ConversationHandler.END

    # ==================================================
    # RANDOM REPLY
    # ==================================================

    async def add_random_reply_start(self, update, context):

        context.user_data.clear()

        await update.callback_query.edit_message_text(
            "🎲 أرسل نص الرد العشوائي:"
        )

        return ADD_RANDOM_REPLY

    async def add_random_reply_text(self, update, context):

        context.user_data["text"] = update.message.text.strip()

        await update.message.reply_text(
            "🖼️ أرسل صورة أو /skip للتخطي"
        )

        return ADD_RANDOM_REPLY

    async def add_random_reply_media(self, update, context):

        text = context.user_data.get("text")

        if not text:
            await update.message.reply_text("❌ لم يتم تحديد النص")
            return ConversationHandler.END

        media_path = None

        if update.message.photo:
            os.makedirs("temp_files/random_replies", exist_ok=True)
            file = await update.message.photo[-1].get_file()
            media_path = f"temp_files/random_replies/{int(datetime.now().timestamp())}.jpg"
            await file.download_to_drive(media_path)

        self.db.add_group_random_reply(
            text,
            media_path,
            update.message.from_user.id
        )

        await update.message.reply_text("✅ تم حفظ الرد العشوائي")

        context.user_data.clear()
        return ConversationHandler.END

    async def skip_random_reply_media(self, update, context):

        text = context.user_data.get("text")

        if not text:
            await update.message.reply_text("❌ لا يوجد نص محفوظ")
            return ConversationHandler.END

        self.db.add_group_random_reply(
            text,
            None,
            update.message.from_user.id
        )

        await update.message.reply_text("✅ تم الحفظ بدون صورة")

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
