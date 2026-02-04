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
    
    async def manage_groups(self, query, context):
        """إدارة المجموعات"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مجموعة", callback_data="add_group")],
            [InlineKeyboardButton("👥 عرض المجموعات", callback_data="show_groups")],
            [InlineKeyboardButton("👥 الانضمام للمجموعات", callback_data="start_join_groups")],
            [InlineKeyboardButton("⏹️ إيقاف الانضمام", callback_data="stop_join_groups")],
            [InlineKeyboardButton("📊 إحصائيات المجموعات", callback_data="group_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👥 **إدارة المجموعات**\n\n"
            "اختر الإجراء الذي تريد تنفيذه:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def add_group_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة مجموعة"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        await query.edit_message_text(
            "👥 **إضافة مجموعات**\n\n"
            "يمكنك إرسال:\n"
            "1. رابط مجموعة واحد\n"
            "2. عدة روابط في رسالة واحدة\n"
            "3. رابط قائمة (addlist)\n"
            "4. رابط دعوة (+joinchat)\n\n"
            "📝 **أمثلة:**\n"
            "• https://t.me/groupname\n"
            "• https://t.me/+invitecode\n"
            "• https://t.me/addlist/listcode\n\n"
            "⚡ **ملاحظة:** التأخير بين كل رابط: 90 ثانية\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        
        context.user_data['adding_group'] = True
        return ADD_GROUP
    
    async def add_group_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة روابط المجموعات"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        message_text = update.message.text
        
        # البحث عن جميع الروابط في النص
        url_pattern = r'(https?://[^\s]+|t\.me/[^\s]+|\+[a-zA-Z0-9_\-]+)'
        links = re.findall(url_pattern, message_text)
        
        if not links:
            await update.message.reply_text(
                "❌ لم يتم العثور على روابط صحيحة!\n"
                "تأكد من إرسال روابط تليجرام صحيحة.\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_GROUP
        
        added_count = 0
        invalid_links = []
        
        await update.message.reply_text(f"⏳ جاري معالجة {len(links)} رابط...")
        
        for link in links:
            # تنظيف الرابط
            cleaned_link = link.strip()
            
            # التحقق من صحة الرابط
            if not self.is_valid_telegram_link(cleaned_link):
                invalid_links.append(cleaned_link)
                continue
            
            # إضافة المجموعة إلى قاعدة البيانات
            if self.db.add_group(cleaned_link, user_id):
                added_count += 1
        
        # عرض النتائج
        response = f"✅ **تمت العملية بنجاح**\n\n"
        response += f"📊 **النتائج:**\n"
        response += f"   • المضافة: {added_count}\n"
        response += f"   • الروابط غير الصالحة: {len(invalid_links)}\n\n"
        
        if added_count > 0:
            response += f"⚡ **سيبدأ الانضمام تلقائياً:**\n"
            response += f"   • التأخير بين الروابط: {DELAY_SETTINGS['join_groups']['between_links']} ثانية\n"
            response += f"   • استخدام جميع الحسابات النشطة\n\n"
            
            # بدء عملية الانضمام بعد تأخير قصير
            asyncio.create_task(self.delayed_join_groups(user_id))
        
        if invalid_links:
            response += f"❌ **روابط غير صالحة:**\n"
            for link in invalid_links[:5]:  # عرض أول 5 روابط غير صالحة فقط
                response += f"   • {link[:50]}...\n"
            if len(invalid_links) > 5:
                response += f"   ... و {len(invalid_links) - 5} رابط إضافي\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_groups")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        context.user_data.pop('adding_group', None)
        return ConversationHandler.END
    
    def is_valid_telegram_link(self, link):
        """التحقق من صحة رابط تليجرام"""
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
        
        for pattern in patterns:
            if re.match(pattern, link):
                return True
        
        return False
    
    async def delayed_join_groups(self, admin_id):
        """بدء الانضمام للمجموعات بعد تأخير قصير"""
        await asyncio.sleep(2)  # انتظار قصير
        
        # التحقق من وجود حسابات
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            logger.warning(f"لا توجد حسابات نشطة للمشرف {admin_id}")
            return
        
        # التحقق من وجود مجموعات معلقة
        groups = self.db.get_groups(admin_id, status='pending')
        if not groups:
            logger.info(f"لا توجد مجموعات معلقة للمشرف {admin_id}")
            return
        
        # بدء عملية الانضمام
        if self.manager.start_join_groups(admin_id):
            logger.info(f"بدأ الانضمام للمجموعات للمشرف {admin_id} بـ {len(accounts)} حساب و {len(groups)} مجموعة")
    
    async def show_groups(self, query, context):
        """عرض جميع المجموعات"""
        user_id = query.from_user.id
        groups = self.db.get_groups(user_id)
        
        if not groups:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد مجموعات مضافة!\n"
                "استخدم زر 'إضافة مجموعة' لإضافة مجموعات جديدة.",
                reply_markup=reply_markup
            )
            return
        
        # إحصائيات سريعة
        pending = len([g for g in groups if g[2] == 'pending'])
        joined = len([g for g in groups if g[2] == 'joined'])
        failed = len([g for g in groups if g[2] == 'failed'])
        
        text = f"👥 **المجموعات المضافة** (⏳{pending} | ✅{joined} | ❌{failed})\n\n"
        
        keyboard = []
        
        for group in groups[:15]:  # عرض أول 15 مجموعة فقط
            group_id, link, status, join_date, added_date, admin_id, last_checked = group
            
            status_emoji = {
                'pending': '⏳',
                'joined': '✅',
                'failed': '❌'
            }.get(status, '❓')
            
            text += f"**#{group_id}** - {link}\n"
            text += f"{status_emoji} {status}\n"
            
            if join_date:
                text += f"📅 انضمام: {join_date[:16]}\n"
            else:
                text += f"📅 مضافة: {added_date[:16]}\n"
            
            text += "─" * 20 + "\n"
            
            # أزرار لكل مجموعة
            keyboard.append([
                InlineKeyboardButton(f"🗑️ حذف #{group_id}", callback_data=f"delete_group_{group_id}"),
                InlineKeyboardButton(f"🔄 تحديث #{group_id}", callback_data=f"update_group_{group_id}")
            ])
        
        if len(groups) > 15:
            text += f"\n... وعرض {len(groups) - 15} مجموعة إضافية"
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث القائمة", callback_data="show_groups"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def delete_group(self, query, context, group_id):
        """حذف مجموعة"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        conn = self.db.conn if hasattr(self.db, 'conn') else None
        if not conn:
            import sqlite3
            conn = sqlite3.connect(self.db.db_name)
        
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM groups WHERE id = ? AND (admin_id = ? OR admin_id = 0)', 
                         (group_id, user_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                await query.edit_message_text(f"✅ تم حذف المجموعة #{group_id} بنجاح")
            else:
                await query.edit_message_text(
                    f"❌ فشل حذف المجموعة #{group_id}\n"
                    "قد تكون المجموعة غير موجودة أو ليس لديك صلاحية لحذفها."
                )
        except Exception as e:
            logger.error(f"خطأ في حذف المجموعة: {e}")
            await query.edit_message_text(f"❌ خطأ في حذف المجموعة: {str(e)}")
        finally:
            if conn:
                conn.close()
        
        await self.show_groups(query, context)
    
    async def start_join_groups(self, query, context):
        """بدء عملية الانضمام للمجموعات"""
        admin_id = query.from_user.id
        
        # التحقق من وجود حسابات
        accounts = self.db.get_active_publishing_accounts(admin_id)
        if not accounts:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد حسابات نشطة!\n"
                "يجب إضافة حسابات أولاً قبل بدء الانضمام للمجموعات.",
                reply_markup=reply_markup
            )
            return
        
        # التحقق من وجود مجموعات معلقة
        groups = self.db.get_groups(admin_id, status='pending')
        if not groups:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد مجموعات معلقة!\n"
                "يجب إضافة مجموعات أولاً.",
                reply_markup=reply_markup
            )
            return
        
        if self.manager.start_join_groups(admin_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"👥 **بدأ الانضمام للمجموعات!**\n\n"
                f"✅ **عدد الحسابات:** {len(accounts)}\n"
                f"✅ **المجموعات المعلقة:** {len(groups)}\n"
                f"⚡ **التأخير بين الروابط:** {DELAY_SETTINGS['join_groups']['between_links']} ثانية\n"
                f"⚡ **بين الدورات:** {DELAY_SETTINGS['join_groups']['between_cycles']} ثواني\n\n"
                f"سيبدأ البوت بالانضمام إلى جميع المجموعات المعلقة الآن.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            logger.info(f"بدأ الانضمام للمجموعات للمشرف {admin_id}")
        else:
            await query.edit_message_text("⚠️ عملية الانضمام تعمل بالفعل!")
    
    async def stop_join_groups(self, query, context):
        """إيقاف عملية الانضمام للمجموعات"""
        admin_id = query.from_user.id
        
        if self.manager.stop_join_groups(admin_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⏹️ تم إيقاف الانضمام للمجموعات!", reply_markup=reply_markup)
            logger.info(f"توقف الانضمام للمجموعات للمشرف {admin_id}")
        else:
            await query.edit_message_text("⚠️ عملية الانضمام غير نشطة!")
    
    async def show_group_stats(self, query, context):
        """عرض إحصائيات المجموعات"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        stats = self.db.get_statistics(user_id)
        
        text = "📊 **إحصائيات المجموعات**\n\n"
        
        text += f"👥 **إجمالي المجموعات:** {stats['groups']['total']}\n"
        text += f"✅ **المنضمة:** {stats['groups']['joined']}\n"
        text += f"⏳ **المعلقة:** {stats['groups']['total'] - stats['groups']['joined']}\n\n"
        
        # معلومات الانضمام
        text += f"⚡ **إعدادات الانضمام:**\n"
        text += f"   • بين الروابط: {DELAY_SETTINGS['join_groups']['between_links']} ثانية\n"
        text += f"   • بين الدورات: {DELAY_SETTINGS['join_groups']['between_cycles']} ثواني\n\n"
        
        # آخر المجموعات المضافة
        groups = self.db.get_groups(user_id)
        if groups:
            text += "📅 **آخر المجموعات:**\n"
            for group in groups[:3]:
                group_id, link, status, join_date, added_date, admin_id, last_checked = group
                status_emoji = {'pending': '⏳', 'joined': '✅', 'failed': '❌'}.get(status, '❓')
                text += f"   • {status_emoji} #{group_id} - {link[:30]}...\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="group_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_groups")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
