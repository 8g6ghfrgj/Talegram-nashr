import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADD_ADMIN, OWNER_ID, MESSAGES

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
    
    def is_owner(self, user_id):
        """التحقق إذا كان المستخدم هو المالك"""
        return user_id == OWNER_ID
    
    async def manage_admins(self, query, context):
        """إدارة المشرفين"""
        user_id = query.from_user.id
        
        # فقط المالك يستطيع إدارة المشرفين
        if not self.is_owner(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                MESSAGES['owner_only'].format(OWNER_ID),
                reply_markup=reply_markup
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")],
            [InlineKeyboardButton("👨‍💼 عرض المشرفين", callback_data="show_admins")],
            [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👨‍💼 **إدارة المشرفين**\n\n"
            f"🔐 **المالك الحالي:** {OWNER_ID}\n"
            f"⚠️ **فقط المالك يستطيع إضافة/حذف المشرفين**\n\n"
            "اختر الإجراء الذي تريد تنفيذه:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def add_admin_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة مشرف - فقط للمالك"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # التحقق من صلاحية المالك
        if not self.is_owner(user_id):
            await query.edit_message_text(
                MESSAGES['owner_only'].format(OWNER_ID)
            )
            return ConversationHandler.END
        
        await query.edit_message_text(
            "👨‍💼 **إضافة مشرف جديد**\n\n"
            "أرسل معرف المستخدم (User ID):\n\n"
            "📝 **ملاحظة:**\n"
            "1. يجب أن يكون المستخدم موجوداً في تليجرام\n"
            "2. يجب أن يكون قد بدأ محادثة مع البوت\n"
            "3. سيتم إضافته كمشرف عادي\n\n"
            "أرسل /cancel للإلغاء",
            parse_mode='Markdown'
        )
        
        context.user_data['adding_admin'] = True
        return ADD_ADMIN
    
    async def add_admin_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة معرف المشرف - فقط للمالك"""
        user_id = update.message.from_user.id
        
        # التحقق من صلاحية المالك
        if not self.is_owner(user_id):
            await update.message.reply_text(
                MESSAGES['owner_only'].format(OWNER_ID)
            )
            return ConversationHandler.END
        
        try:
            # تحويل النص إلى رقم
            user_id_to_add = int(update.message.text.strip())
            
            # التحقق من أن المعرف ليس للمالك نفسه
            if user_id_to_add == OWNER_ID:
                await update.message.reply_text(
                    "❌ لا يمكن إضافة المالك نفسه كمشرف!\n"
                    "المالك لديه جميع الصلاحيات افتراضياً."
                )
                return ADD_ADMIN
            
            # التحقق من أن المعرف ليس سالباً أو صفراً
            if user_id_to_add <= 0:
                await update.message.reply_text(
                    "❌ معرف المستخدم غير صحيح!\n"
                    "يجب أن يكون رقماً موجباً.\n"
                    "حاول مرة أخرى أو أرسل /cancel للإلغاء"
                )
                return ADD_ADMIN
            
            # الحصول على معلومات المستخدم من التليجرام
            try:
                user = await context.bot.get_chat(user_id_to_add)
                username = f"@{user.username}" if user.username else "لا يوجد"
                full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
                
            except Exception as e:
                logger.warning(f"لم يتمكن من الحصول على معلومات المستخدم {user_id_to_add}: {e}")
                username = "غير معروف"
                full_name = f"مستخدم {user_id_to_add}"
            
            # إضافة المشرف إلى قاعدة البيانات
            success, message = self.db.add_admin(user_id_to_add, username, full_name, False)
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_admins")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ {message}\n\n"
                f"👤 **المستخدم:** {full_name}\n"
                f"🆔 **المعرف:** {user_id_to_add}\n"
                f"🔗 **المستخدم:** {username}\n"
                f"👑 **الدور:** مشرف عادي\n\n"
                f"⚠️ **تنبيه:** يجب أن يبدأ المشرف الجديد محادثة مع البوت باستخدام /start",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ معرف المستخدم يجب أن يكون رقماً!\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_ADMIN
        except Exception as e:
            logger.error(f"خطأ في إضافة المشرف: {e}")
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}\n"
                "حاول مرة أخرى أو أرسل /cancel للإلغاء"
            )
            return ADD_ADMIN
        
        context.user_data.pop('adding_admin', None)
        return ConversationHandler.END
    
    async def show_admins(self, query, context):
        """عرض جميع المشرفين"""
        user_id = query.from_user.id
        
        # فقط المالك والمشرفون يستطيعون رؤية القائمة
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        admins = self.db.get_admins()
        
        if not admins:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد مشرفين مضافة!\n"
                "فقط المالك يمكنه إضافة مشرفين.",
                reply_markup=reply_markup
            )
            return
        
        text = "👨‍💼 **المشرفين المضافين**\n\n"
        
        keyboard = []
        can_delete = self.is_owner(user_id)  # فقط المالك يستطيع الحذف
        
        for admin in admins:
            admin_id, user_id_admin, username, full_name, added_date, is_super_admin = admin
            
            # تحديد الدور
            if user_id_admin == OWNER_ID:
                role = "👑 المالك الرئيسي"
            elif is_super_admin:
                role = "🟢 مشرف رئيسي"
            else:
                role = "🔵 مشرف عادي"
            
            text += f"**#{admin_id}** - {full_name}\n"
            text += f"🆔 **المعرف:** {user_id_admin}\n"
            text += f"🔗 **المستخدم:** {username}\n"
            text += f"👑 **الدور:** {role}\n"
            text += f"📅 **تاريخ الإضافة:** {added_date[:16]}\n"
            text += "─" * 20 + "\n"
            
            # إضافة زر الحذف فقط للمالك
            if can_delete and user_id_admin != OWNER_ID:  # لا يمكن حذف المالك
                keyboard.append([InlineKeyboardButton(f"🗑️ حذف #{admin_id}", callback_data=f"delete_admin_{admin_id}")])
        
        # إذا لم يكن المستخدم مالكاً، لا يعرض أزرار الحذف
        if not can_delete:
            text += "\n⚠️ **فقط المالك يستطيع حذف المشرفين**\n"
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث القائمة", callback_data="show_admins"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def delete_admin(self, query, context, admin_id):
        """حذف مشرف - فقط للمالك"""
        user_id = query.from_user.id
        
        # التحقق من صلاحية المالك
        if not self.is_owner(user_id):
            await query.edit_message_text(
                MESSAGES['owner_only'].format(OWNER_ID)
            )
            return
        
        # الحصول على معلومات المشرف قبل الحذف
        admins = self.db.get_admins()
        admin_name = ""
        admin_user_id = 0
        
        for admin in admins:
            if admin[0] == admin_id:
                admin_name = admin[3]
                admin_user_id = admin[1]
                break
        
        # منع حذف المالك نفسه
        if admin_user_id == OWNER_ID:
            await query.edit_message_text("❌ لا يمكن حذف المالك الرئيسي!")
            await self.show_admins(query, context)
            return
        
        # حذف المشرف
        if self.db.delete_admin(admin_id):
            await query.edit_message_text(
                f"✅ تم حذف المشرف #{admin_id} ({admin_name}) بنجاح"
            )
        else:
            await query.edit_message_text(
                f"❌ فشل حذف المشرف #{admin_id}\n"
                "قد يكون المشرف غير موجود."
            )
        
        # العودة إلى قائمة المشرفين
        await self.show_admins(query, context)
    
    async def show_system_stats(self, query, context):
        """عرض إحصائيات النظام"""
        user_id = query.from_user.id
        
        # فقط المالك يستطيع رؤية إحصائيات النظام
        if not self.is_owner(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                MESSAGES['owner_only'].format(OWNER_ID),
                reply_markup=reply_markup
            )
            return
        
        # الحصول على إحصائيات النظام
        stats = self.db.get_statistics()
        
        text = "📊 **إحصائيات النظام**\n\n"
        
        text += "👥 **الحسابات:**\n"
        text += f"   • الإجمالي: {stats['accounts']['total']}\n"
        text += f"   • النشطة: {stats['accounts']['active']}\n"
        text += f"   • غير النشطة: {stats['accounts']['total'] - stats['accounts']['active']}\n\n"
        
        text += f"📢 **الإعلانات:** {stats['ads']}\n\n"
        
        text += "👥 **المجموعات:**\n"
        text += f"   • الإجمالي: {stats['groups']['total']}\n"
        text += f"   • المنضمة: {stats['groups']['joined']}\n"
        text += f"   • المعلقة: {stats['groups']['total'] - stats['groups']['joined']}\n\n"
        
        # الحصول على عدد المشرفين
        admins = self.db.get_admins()
        super_admins = len([a for a in admins if a[5]])  # is_super_admin
        normal_admins = len([a for a in admins if not a[5]])
        
        text += "👨‍💼 **المشرفين:**\n"
        text += f"   • المالك: 1\n"
        text += f"   • المشرفين الرئيسيين: {super_admins}\n"
        text += f"   • المشرفين العاديين: {normal_admins}\n"
        text += f"   • الإجمالي: {len(admins)}\n\n"
        
        # الحصول على الردود
        private_replies = self.db.get_private_replies(decode=False)
        text_replies = self.db.get_group_text_replies(decode=False)
        photo_replies = self.db.get_group_photo_replies(decode=False)
        random_replies = self.db.get_group_random_replies(decode=False)
        
        text += "💬 **الردود:**\n"
        text += f"   • في الخاص: {len(private_replies)}\n"
        text += f"   • نصية في القروبات: {len(text_replies)}\n"
        text += f"   • مع صور في القروبات: {len(photo_replies)}\n"
        text += f"   • عشوائية في القروبات: {len(random_replies)}\n\n"
        
        # الحصول على آخر النشاطات
        logs = self.db.get_logs(limit=10)
        if logs:
            text += "📋 **آخر النشاطات:**\n"
            for log in logs[:5]:
                log_id, log_admin, action, details, timestamp = log
                text += f"   • {action}: {details[:50]}...\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def toggle_admin_status(self, query, context, admin_id):
        """تبديل حالة المشرف (للمالك فقط)"""
        user_id = query.from_user.id
        
        if not self.is_owner(user_id):
            await query.edit_message_text(
                MESSAGES['owner_only'].format(OWNER_ID)
            )
            return
        
        conn = self.db.conn if hasattr(self.db, 'conn') else None
        if not conn:
            import sqlite3
            conn = sqlite3.connect(self.db.db_name)
        
        cursor = conn.cursor()
        
        try:
            # الحصول على الحالة الحالية
            cursor.execute('SELECT is_super_admin FROM admins WHERE id = ?', (admin_id,))
            result = cursor.fetchone()
            
            if not result:
                await query.edit_message_text(f"❌ المشرف #{admin_id} غير موجود!")
                return
            
            current_status = result[0]
            new_status = 0 if current_status else 1
            
            # تحديث الحالة
            cursor.execute('UPDATE admins SET is_super_admin = ? WHERE id = ?', (new_status, admin_id))
            conn.commit()
            
            status_text = "مشرف رئيسي" if new_status else "مشرف عادي"
            await query.edit_message_text(f"✅ تم تغيير دور المشرف #{admin_id} إلى: {status_text}")
            
        except Exception as e:
            logger.error(f"خطأ في تبديل حالة المشرف: {e}")
            await query.edit_message_text(f"❌ خطأ في تغيير الدور: {str(e)}")
        finally:
            if conn:
                conn.close()
        
        await self.show_admins(query, context)
    
    async def export_data(self, query, context):
        """تصدير البيانات (للمالك فقط)"""
        user_id = query.from_user.id
        
        if not self.is_owner(user_id):
            await query.edit_message_text(
                MESSAGES['owner_only'].format(OWNER_ID)
            )
            return
        
        await query.edit_message_text(
            "📤 **تصدير البيانات**\n\n"
            "جاري تجهيز البيانات للتصدير...\n"
            "قد يستغرق هذا بعض الوقت."
        )
        
        try:
            # إنشاء ملف تصدير
            import json
            from datetime import datetime
            
            data = {
                'export_date': datetime.now().isoformat(),
                'owner_id': OWNER_ID,
                'statistics': self.db.get_statistics(),
                'accounts': [],
                'admins': [],
                'ads': [],
                'groups': []
            }
            
            # تصدير الحسابات (بدون session strings لأمان)
            accounts = self.db.get_accounts()
            for acc in accounts:
                acc_id, session_string, phone, name, username, is_active, added_date, status, last_publish = acc
                data['accounts'].append({
                    'id': acc_id,
                    'phone': phone,
                    'name': name,
                    'username': username,
                    'is_active': bool(is_active),
                    'added_date': added_date
                })
            
            # تصدير المشرفين
            admins = self.db.get_admins()
            for admin in admins:
                admin_id, user_id_admin, username, full_name, added_date, is_super_admin = admin
                data['admins'].append({
                    'id': admin_id,
                    'user_id': user_id_admin,
                    'username': username,
                    'full_name': full_name,
                    'is_super_admin': bool(is_super_admin),
                    'added_date': added_date
                })
            
            # تصدير الإعلانات
            ads = self.db.get_ads(decode=True)
            for ad in ads:
                ad_id, ad_type, ad_text, media_path, file_type, added_date, ad_admin_id, is_encoded = ad
                data['ads'].append({
                    'id': ad_id,
                    'type': ad_type,
                    'text': ad_text[:100] if ad_text else None,
                    'file_type': file_type,
                    'added_date': added_date
                })
            
            # تصدير المجموعات
            groups = self.db.get_groups()
            for group in groups:
                group_id, link, status, join_date, added_date, admin_id, last_checked = group
                data['groups'].append({
                    'id': group_id,
                    'link': link,
                    'status': status,
                    'join_date': join_date,
                    'added_date': added_date
                })
            
            # حفظ الملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"system_export_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admins")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ **تم تصدير البيانات بنجاح!**\n\n"
                f"📁 **اسم الملف:** {filename}\n"
                f"📊 **عدد السجلات:**\n"
                f"   • الحسابات: {len(data['accounts'])}\n"
                f"   • المشرفين: {len(data['admins'])}\n"
                f"   • الإعلانات: {len(data['ads'])}\n"
                f"   • المجموعات: {len(data['groups'])}\n\n"
                f"⚠️ **ملاحظة:** تم حذف session strings لأسباب أمنية.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في تصدير البيانات: {e}")
            await query.edit_message_text(
                f"❌ **خطأ في تصدير البيانات:**\n{str(e)}"
      )
