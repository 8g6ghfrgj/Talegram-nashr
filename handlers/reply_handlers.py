import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    ADD_PRIVATE_REPLY, ADD_GROUP_TEXT, ADD_GROUP_PHOTO, 
    ADD_RANDOM_REPLY, ADD_PRIVATE_TEXT, MESSAGES
)

logger = logging.getLogger(__name__)

class ReplyHandlers:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
    
    async def manage_replies(self, query, context):
        """إدارة الردود"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        keyboard = [
            [InlineKeyboardButton("💬 الردود في الخاص", callback_data="private_replies")],
            [InlineKeyboardButton("👥 الردود في القروبات", callback_data="group_replies")],
            [InlineKeyboardButton("🗑️ عرض الردود للحذف", callback_data="show_replies")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💬 **إدارة الردود**\n\n"
            "اختر نوع الردود التي تريد إدارتها:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_replies_menu(self, query, context):
        """عرض قائمة حذف الردود"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        keyboard = [
            [InlineKeyboardButton("🗑️ حذف ردود الخاصة", callback_data="show_private_replies_delete")],
            [InlineKeyboardButton("🗑️ حذف ردود القروبات النصية", callback_data="show_text_replies_delete")],
            [InlineKeyboardButton("🗑️ حذف ردود القروبات مع صور", callback_data="show_photo_replies_delete")],
            [InlineKeyboardButton("🗑️ حذف ردود عشوائية", callback_data="show_random_replies_delete")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_replies")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ **حذف الردود**\n\n"
            "اختر نوع الردود التي تريد حذفها:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def manage_private_replies(self, query, context):
        """إدارة الردود الخاصة"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        replies = self.db.get_private_replies(user_id)
        
        text = "💬 **الردود في الخاص**\n\n"
        
        if replies:
            for reply in replies[:10]:  # عرض أول 10 ردود فقط
                reply_id, reply_text, is_active, added_date, reply_admin_id, is_encoded = reply
                status = "🟢 نشط" if is_active else "🔴 غير نشط"
                
                text += f"**#{reply_id}**\n"
                text += f"📝 {reply_text[:50]}...\n"
                text += f"الحالة: {status}\n"
                text += f"📅 {added_date[:16]}\n"
                text += "─" * 20 + "\n"
            
            if len(replies) > 10:
                text += f"\n... وعرض {len(replies) - 10} رد إضافي"
        else:
            text += "❌ لا توجد ردود مضافة\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة رد", callback_data="add_private_reply")],
            [InlineKeyboardButton("🚀 بدء الرد في الخاص", callback_data="start_private_reply")],
            [InlineKeyboardButton("⏹️ إيقاف الرد في الخاص", callback_data="stop_private_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_replies")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def add_private_reply_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة رد خاص"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        await query.edit_message_text(
            "💬 **إضافة رد في الخاص**\n\n"
            "أرسل نص الرد الآن:\n\n"
            "⚠️ **ملاحظة:** سيقوم البوت بالرد تلقائياً على جميع الرسائل الخاصة\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        
        context.user_data['adding_private_reply'] = True
        return ADD_PRIVATE_TEXT
    
    async def add_private_reply_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة نص الرد الخاص"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        reply_text = update.message.text
        
        if not reply_text or len(reply_text.strip()) < 2:
            await update.message.reply_text(
                "❌ النص قصير جداً!\n"
                "يرجى إرسال نص أطول (على الأقل حرفين)\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_PRIVATE_TEXT
        
        # إضافة الرد إلى قاعدة البيانات
        if self.db.add_private_reply(reply_text, user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_private_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ تم إضافة الرد في الخاص بنجاح\n\n"
                f"📝 **النص:**\n{reply_text[:100]}...",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ فشل إضافة الرد")
        
        context.user_data.pop('adding_private_reply', None)
        return ConversationHandler.END
    
    async def show_private_replies_delete(self, query, context):
        """عرض الردود الخاصة للحذف"""
        user_id = query.from_user.id
        replies = self.db.get_private_replies(user_id)
        
        if not replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود خاصة مضافة",
                reply_markup=reply_markup
            )
            return
        
        text = "🗑️ **الردود في الخاص للحذف:**\n\n"
        
        keyboard = []
        
        for reply in replies[:15]:  # عرض أول 15 رد فقط
            reply_id, reply_text, is_active, added_date, reply_admin_id, is_encoded = reply
            
            text += f"**#{reply_id}**\n"
            text += f"📝 {reply_text[:50]}...\n"
            text += f"الحالة: {'🟢 نشط' if is_active else '🔴 غير نشط'}\n"
            text += "─" * 20 + "\n"
            
            keyboard.append([InlineKeyboardButton(f"🗑️ حذف #{reply_id}", callback_data=f"delete_private_reply_{reply_id}")])
        
        if len(replies) > 15:
            text += f"\n... وعرض {len(replies) - 15} رد إضافي"
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث القائمة", callback_data="show_private_replies_delete"),
            InlineKeyboardButton("🔙 رجوع", callback_data="show_replies")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def delete_private_reply(self, query, context, reply_id):
        """حذف رد خاص"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        if self.db.delete_private_reply(reply_id, user_id):
            await query.edit_message_text(f"✅ تم حذف الرد الخاص #{reply_id} بنجاح")
        else:
            await query.edit_message_text(
                f"❌ فشل حذف الرد الخاص #{reply_id}\n"
                "قد يكون الرد غير موجود أو ليس لديك صلاحية لحذفه."
            )
        
        await self.show_private_replies_delete(query, context)
    
    async def manage_group_replies(self, query, context):
        """إدارة الردود في القروبات"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        text_replies = self.db.get_group_text_replies(user_id)
        photo_replies = self.db.get_group_photo_replies(user_id)
        random_replies = self.db.get_group_random_replies(user_id)
        
        text = "👥 **الردود في القروبات**\n\n"
        
        text += "**الردود على رسائل محددة:**\n"
        if text_replies or photo_replies:
            total_specific = len(text_replies) + len(photo_replies)
            text += f"📊 الإجمالي: {total_specific} رد\n\n"
            
            if text_replies:
                text += "📝 **الردود النصية:**\n"
                for reply in text_replies[:3]:
                    reply_id, trigger, reply_text, is_active, added_date, reply_admin_id, is_encoded = reply
                    text += f"   • #{reply_id} على: {trigger}\n"
            
            if photo_replies:
                text += "\n🖼️ **الردود مع الصور:**\n"
                for reply in photo_replies[:3]:
                    reply_id, trigger, reply_text, media_path, is_active, added_date, reply_admin_id, is_encoded = reply
                    text += f"   • #{reply_id} على: {trigger}\n"
        else:
            text += "❌ لا توجد ردود مضافة\n"
        
        text += "\n**الردود العشوائية (100%):**\n"
        if random_replies:
            text += f"📊 الإجمالي: {len(random_replies)} رد\n\n"
            for reply in random_replies[:3]:
                reply_id, reply_text, media_path, is_active, added_date, reply_admin_id, is_encoded, has_media = reply
                media_type = "مع صورة" if has_media else "نص فقط"
                text += f"   • #{reply_id} - {media_type}\n"
        else:
            text += "❌ لا توجد ردود عشوائية مضافة\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة رد محدد", callback_data="add_group_text_reply")],
            [InlineKeyboardButton("➕ إضافة رد مع صورة", callback_data="add_group_photo_reply")],
            [InlineKeyboardButton("➕ إضافة رد عشوائي", callback_data="add_random_reply")],
            [InlineKeyboardButton("🚀 بدء الردود المحددة", callback_data="start_group_reply")],
            [InlineKeyboardButton("⏹️ إيقاف الردود المحددة", callback_data="stop_group_reply")],
            [InlineKeyboardButton("🚀 بدء الردود العشوائية", callback_data="start_random_reply")],
            [InlineKeyboardButton("⏹️ إيقاف الردود العشوائية", callback_data="stop_random_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_replies")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def add_group_text_reply_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة رد نصي في القروبات"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        await query.edit_message_text(
            "👥 **إضافة رد نصي في القروبات**\n\n"
            "أرسل النص الذي سيتم الرد عليه:\n\n"
            "مثال: مرحبا، السلام، اهلا\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        
        context.user_data['adding_group_text_reply'] = True
        return ADD_GROUP_TEXT
    
    async def add_group_text_reply_trigger(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة النص المحفز للرد النصي"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        trigger = update.message.text.strip()
        
        if not trigger or len(trigger) < 2:
            await update.message.reply_text(
                "❌ النص المحفز قصير جداً!\n"
                "يرجى إرسال نص أطول (على الأقل حرفين)\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_GROUP_TEXT
        
        context.user_data['group_text_trigger'] = trigger
        
        await update.message.reply_text(
            "👥 **إضافة رد نصي في القروبات**\n\n"
            "أرسل نص الرد الآن:\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        return ADD_GROUP_TEXT
    
    async def add_group_text_reply_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة نص الرد النصي"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        trigger = context.user_data.get('group_text_trigger')
        reply_text = update.message.text
        
        if not trigger:
            await update.message.reply_text("❌ لم يتم تحديد النص المحفز!")
            return ConversationHandler.END
        
        if not reply_text or len(reply_text.strip()) < 2:
            await update.message.reply_text(
                "❌ نص الرد قصير جداً!\n"
                "يرجى إرسال نص أطول (على الأقل حرفين)"
            )
            return ADD_GROUP_TEXT
        
        # إضافة الرد النصي إلى قاعدة البيانات
        if self.db.add_group_text_reply(trigger, reply_text, user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ تم إضافة الرد النصي في القروبات بنجاح\n\n"
                f"📝 **على:** {trigger}\n"
                f"💬 **الرد:** {reply_text[:100]}...",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ فشل إضافة الرد النصي")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def add_group_photo_reply_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة رد مع صورة في القروبات"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        await query.edit_message_text(
            "👥 **إضافة رد مع صورة في القروبات**\n\n"
            "أرسل النص الذي سيتم الرد عليه:\n\n"
            "مثال: صورة، صور، فوتو\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        
        context.user_data['adding_group_photo_reply'] = True
        return ADD_GROUP_PHOTO
    
    async def add_group_photo_reply_trigger(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة النص المحفز للرد مع صورة"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        trigger = update.message.text.strip()
        
        if not trigger or len(trigger) < 2:
            await update.message.reply_text(
                "❌ النص المحفز قصير جداً!\n"
                "يرجى إرسال نص أطول (على الأقل حرفين)\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_GROUP_PHOTO
        
        context.user_data['group_photo_trigger'] = trigger
        
        await update.message.reply_text(
            "👥 **إضافة رد مع صورة في القروبات**\n\n"
            "أرسل نص الرد (يمكنك تركها فارغة):\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        return ADD_GROUP_PHOTO
    
    async def add_group_photo_reply_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة نص الرد مع صورة"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        trigger = context.user_data.get('group_photo_trigger')
        reply_text = update.message.text
        
        if not trigger:
            await update.message.reply_text("❌ لم يتم تحديد النص المحفز!")
            return ConversationHandler.END
        
        context.user_data['group_photo_text'] = reply_text
        
        await update.message.reply_text(
            "👥 **إضافة رد مع صورة في القروبات**\n\n"
            "أرسل الصورة الآن:\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        return ADD_GROUP_PHOTO
    
    async def add_group_photo_reply_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة صورة الرد"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        if not update.message.photo:
            await update.message.reply_text(
                "❌ يرجى إرسال صورة صالحة!\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_GROUP_PHOTO
        
        trigger = context.user_data.get('group_photo_trigger')
        reply_text = context.user_data.get('group_photo_text', '')
        
        if not trigger:
            await update.message.reply_text("❌ لم يتم تحديد النص المحفز!")
            return ConversationHandler.END
        
        try:
            os.makedirs("temp_files/group_replies", exist_ok=True)
            
            # حفظ الصورة
            file_id = update.message.photo[-1].file_id
            file = await context.bot.get_file(file_id)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"temp_files/group_replies/photo_{timestamp}.jpg"
            await file.download_to_drive(file_path)
            
            # إضافة الرد مع الصورة إلى قاعدة البيانات
            if self.db.add_group_photo_reply(trigger, reply_text, file_path, user_id):
                keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_group_replies")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                response_text = f"✅ تم إضافة الرد مع الصورة في القروبات بنجاح\n\n"
                response_text += f"📝 **على:** {trigger}\n"
                if reply_text:
                    response_text += f"💬 **الرد:** {reply_text[:100]}...\n"
                response_text += f"🖼️ **الصورة:** {os.path.basename(file_path)}"
                
                await update.message.reply_text(
                    response_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ فشل إضافة الرد مع الصورة")
        
        except Exception as e:
            logger.error(f"خطأ في حفظ صورة الرد: {str(e)}")
            await update.message.reply_text("❌ حدث خطأ أثناء حفظ الصورة")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def add_random_reply_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة رد عشوائي"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        await query.edit_message_text(
            "🎲 **إضافة رد عشوائي في القروبات**\n\n"
            "أرسل نص الرد العشوائي الآن:\n\n"
            "⚠️ **ملاحظة:** سيرد البوت على 100% من الرسائل في القروبات\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        
        context.user_data['adding_random_reply'] = True
        return ADD_RANDOM_REPLY
    
    async def add_random_reply_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة نص الرد العشوائي"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        reply_text = update.message.text
        
        if not reply_text or len(reply_text.strip()) < 2:
            await update.message.reply_text(
                "❌ النص قصير جداً!\n"
                "يرجى إرسال نص أطول (على الأقل حرفين)\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_RANDOM_REPLY
        
        context.user_data['random_reply_text'] = reply_text
        
        await update.message.reply_text(
            "🎲 **إضافة رد عشوائي في القروبات**\n\n"
            "هل تريد إضافة صورة مع الرد؟\n\n"
            "✅ أرسل صورة الآن\n"
            "❌ أو أرسل /skip لتخطي إضافة صورة\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        return ADD_RANDOM_REPLY
    
    async def add_random_reply_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة وسائط الرد العشوائي"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        reply_text = context.user_data.get('random_reply_text')
        
        if not reply_text:
            await update.message.reply_text("❌ لم يتم تحديد نص الرد!")
            return ConversationHandler.END
        
        media_path = None
        
        if update.message.photo:
            try:
                os.makedirs("temp_files/random_replies", exist_ok=True)
                
                file_id = update.message.photo[-1].file_id
                file = await context.bot.get_file(file_id)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                media_path = f"temp_files/random_replies/photo_{timestamp}.jpg"
                await file.download_to_drive(media_path)
                
            except Exception as e:
                logger.error(f"خطأ في حفظ صورة الرد العشوائي: {str(e)}")
        
        # إضافة الرد العشوائي إلى قاعدة البيانات
        if self.db.add_group_random_reply(reply_text, media_path, user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            response_text = "✅ تم إضافة الرد العشوائي بنجاح\n\n"
            response_text += f"📝 **النص:** {reply_text[:100]}...\n"
            response_text += f"🖼️ **الصورة:** {'✅ مضافة' if media_path else '❌ بدون صورة'}"
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ فشل إضافة الرد العشوائي")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def skip_random_reply_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تخطي إضافة وسائط للرد العشوائي"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        reply_text = context.user_data.get('random_reply_text')
        
        if not reply_text:
            await update.message.reply_text("❌ لم يتم تحديد نص الرد!")
            return ConversationHandler.END
        
        # إضافة الرد العشوائي بدون صورة
        if self.db.add_group_random_reply(reply_text, None, user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ تم إضافة الرد العشوائي النصي بنجاح\n\n"
                f"📝 **النص:** {reply_text[:100]}...",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ فشل إضافة الرد العشوائي")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def start_private_reply(self, query, context):
        """بدء الرد التلقائي في الخاص"""
        admin_id = query.from_user.id
        
        # التحقق من وجود حسابات
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_private_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد حسابات نشطة!",
                reply_markup=reply_markup
            )
            return
        
        # التحقق من وجود ردود
        replies = self.db.get_private_replies(admin_id)
        if not replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_private_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود خاصة!",
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_private_reply(admin_id):
            keyboard = [[InlineKeyboardButton("⏹️ إيقاف الرد", callback_data="stop_private_reply")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "💬 **تم بدء الرد في الخاص بأقصى سرعة!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **عدد الردود:** {len(replies)}\n"
                f"⚡ **بين الردود:** 0.05 ثانية\n"
                f"⚡ **بين الدورات:** 3 ثواني\n\n"
                "سيبدأ البوت بالرد على الرسائل الخاصة الآن بأقصى سرعة ممكنة.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ الرد في الخاص يعمل بالفعل!")
    
    async def stop_private_reply(self, query, context):
        """إيقاف الرد التلقائي في الخاص"""
        admin_id = query.from_user.id
        
        if self.manager.stop_private_reply(admin_id):
            await query.edit_message_text("⏹️ تم إيقاف الرد في الخاص!")
        else:
            await query.edit_message_text("⚠️ الرد في الخاص غير نشط!")
    
    async def start_group_reply(self, query, context):
        """بدء الرد التلقائي في القروبات"""
        admin_id = query.from_user.id
        
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد حسابات نشطة!",
                reply_markup=reply_markup
            )
            return
        
        text_replies = self.db.get_group_text_replies(admin_id)
        photo_replies = self.db.get_group_photo_replies(admin_id)
        
        if not text_replies and not photo_replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود مضافة!",
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_group_reply(admin_id):
            keyboard = [[InlineKeyboardButton("⏹️ إيقاف الرد", callback_data="stop_group_reply")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👥 **تم بدء الرد في القروبات بأقصى سرعة!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **عدد الردود النصية:** {len(text_replies)}\n"
                f"✅ **عدد الردود مع الصور:** {len(photo_replies)}\n"
                f"⚡ **بين الردود:** 0.05 ثانية\n"
                f"⚡ **بين الدورات:** 3 ثواني\n\n"
                "سيبدأ البوت بالرد على الرسائل في القروبات الآن بأقصى سرعة ممكنة.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ الرد في القروبات يعمل بالفعل!")
    
    async def stop_group_reply(self, query, context):
        """إيقاف الرد التلقائي في القروبات"""
        admin_id = query.from_user.id
        
        if self.manager.stop_group_reply(admin_id):
            await query.edit_message_text("⏹️ تم إيقاف الرد في القروبات!")
        else:
            await query.edit_message_text("⚠️ الرد في القروبات غير نشط!")
    
    async def start_random_reply(self, query, context):
        """بدء الردود العشوائية في القروبات"""
        admin_id = query.from_user.id
        
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد حسابات نشطة!",
                reply_markup=reply_markup
            )
            return
        
        random_replies = self.db.get_group_random_replies(admin_id)
        if not random_replies:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_group_replies")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد ردود عشوائية مضافة!",
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_random_reply(admin_id):
            keyboard = [[InlineKeyboardButton("⏹️ إيقاف الرد العشوائي", callback_data="stop_random_reply")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🎲 **تم بدء الردود العشوائية بأقصى سرعة!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **عدد الردود العشوائية:** {len(random_replies)}\n"
                f"✅ **الرد على 100% من الرسائل**\n"
                f"⚡ **بين الردود:** 0.05 ثانية\n"
                f"⚡ **بين الدورات:** 3 ثواني\n\n"
                "سيبدأ البوت بالرد العشوائي في القروبات الآن بأقصى سرعة ممكنة.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ الرد العشوائي يعمل بالفعل!")
    
    async def stop_random_reply(self, query, context):
        """إيقاف الردود العشوائية في القروبات"""
        admin_id = query.from_user.id
        
        if self.manager.stop_random_reply(admin_id):
            await query.edit_message_text("⏹️ تم إيقاف الرد العشوائي!")
        else:
            await query.edit_message_text("⚠️ الرد العشوائي غير نشط!")
    
    async def start_publishing(self, query, context):
        """بدء النشر التلقائي"""
        admin_id = query.from_user.id
        
        # التحقق من وجود حسابات
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد حسابات نشطة!\n\n"
                "يجب إضافة حسابات أولاً قبل بدء النشر.",
                reply_markup=reply_markup
            )
            return
        
        # التحقق من وجود إعلانات
        ads = self.db.get_ads(admin_id)
        if not ads:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد إعلانات!\n\n"
                "يجب إضافة إعلانات أولاً قبل بدء النشر.",
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_publishing(admin_id):
            keyboard = [
                [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_publishing")],
                [InlineKeyboardButton("💬 بدء الرد في الخاص", callback_data="start_private_reply")],
                [InlineKeyboardButton("👥 بدء الرد في القروبات", callback_data="start_group_reply")],
                [InlineKeyboardButton("🎲 بدء الرد العشوائي", callback_data="start_random_reply")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🚀 **تم بدء النشر بأقصى سرعة!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **عدد الإعلانات:** {len(ads)}\n"
                f"⏱️ **تأخير نشر القروبات:** 60 ثانية\n"
                f"⚡ **بين الإعلانات:** 0.1 ثانية\n"
                f"⚡ **بين المجموعات:** 0.2 ثانية\n"
                f"⚡ **بين الدورات:** 30 ثانية\n\n"
                "سيبدأ البوت بالنشر في جميع المجموعات الآن مع تأمين الحسابات.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ النشر يعمل بالفعل!")
    
    async def stop_publishing(self, query, context):
        """إيقاف النشر التلقائي"""
        admin_id = query.from_user.id
        
        if self.manager.stop_publishing(admin_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⏹️ تم إيقاف النشر!", reply_markup=reply_markup)
        else:
            await query.edit_message_text("⚠️ النشر غير نشط!")
