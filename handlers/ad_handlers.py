import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADD_AD_TYPE, ADD_AD_TEXT, ADD_AD_MEDIA, AD_TYPES, MESSAGES
from database.text_encoder import TextEncoder

logger = logging.getLogger(__name__)

class AdHandlers:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.text_encoder = TextEncoder()
    
    async def manage_ads(self, query, context):
        """إدارة الإعلانات"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة إعلان", callback_data="add_ad")],
            [InlineKeyboardButton("📋 عرض الإعلانات", callback_data="show_ads")],
            [InlineKeyboardButton("📊 إحصائيات الإعلانات", callback_data="ad_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 **إدارة الإعلانات**\n\n"
            "اختر الإجراء الذي تريد تنفيذه:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def add_ad_start(self, query, context):
        """بدء إضافة إعلان"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton(AD_TYPES['text'], callback_data="ad_type_text")],
            [InlineKeyboardButton(AD_TYPES['photo'], callback_data="ad_type_photo")],
            [InlineKeyboardButton(AD_TYPES['contact'], callback_data="ad_type_contact")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 **إضافة إعلان جديد**\n\n"
            "اختر نوع الإعلان الذي تريد إضافته:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def add_ad_type(self, query, context):
        """معالجة نوع الإعلان"""
        user_id = query.from_user.id
        data = query.data
        
        if not data.startswith("ad_type_"):
            return
        
        ad_type = data.replace("ad_type_", "")
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        context.user_data['ad_type'] = ad_type
        
        if ad_type == 'contact':
            await query.edit_message_text(
                f"📞 **إضافة جهة اتصال**\n\n"
                f"يمكنك:\n"
                f"1. أرسل ملف VCF\n"
                f"2. أو أرسل جهة اتصال مباشرة\n\n"
                f"سيتم حفظه باسم: تسوي سكليف صحتي واتساب.vcf\n\n"
                f"أرسل /cancel للإلغاء",
                parse_mode='Markdown'
            )
            return ADD_AD_MEDIA
        else:
            file_type_text = {
                'text': 'نص الإعلان',
                'photo': 'نص الإعلان للصورة',
            }
            
            await query.edit_message_text(
                f"📝 **{file_type_text.get(ad_type, 'إضافة نص الإعلان')}**\n\n"
                f"أرسل النص الآن:\n\n"
                f"أو أرسل /cancel للإلغاء",
                parse_mode='Markdown'
            )
            return ADD_AD_TEXT
    
    async def add_ad_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة نص الإعلان"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        ad_type = context.user_data.get('ad_type')
        if not ad_type:
            await update.message.reply_text("❌ خطأ: لم يتم تحديد نوع الإعلان")
            return ConversationHandler.END
        
        ad_text = update.message.text
        
        if not ad_text or len(ad_text.strip()) < 2:
            await update.message.reply_text(
                "❌ النص قصير جداً!\n"
                "يرجى إرسال نص أطول (على الأقل حرفين)"
            )
            return ADD_AD_TEXT
        
        context.user_data['ad_text'] = ad_text
        
        if ad_type == 'text':
            # حفظ الإعلان النصي مباشرة
            success, message = self.db.add_ad('text', ad_text, admin_id=user_id)
            
            if success:
                keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_ads")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ {message}\n\n"
                    f"📝 **الإعلان النصي:**\n{ad_text[:100]}...",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ {message}")
            
            return ConversationHandler.END
        
        elif ad_type == 'photo':
            await update.message.reply_text(
                "🖼️ **إضافة صورة للإعلان**\n\n"
                "أرسل الصورة الآن:\n\n"
                "أو أرسل /cancel للإلغاء",
                parse_mode='Markdown'
            )
            return ADD_AD_MEDIA
    
    def create_vcf_from_contact(self, contact):
        """إنشاء ملف VCF من بيانات جهة الاتصال"""
        try:
            vcf_lines = []
            vcf_lines.append("BEGIN:VCARD")
            vcf_lines.append("VERSION:3.0")
            
            full_name = ""
            if contact.first_name:
                full_name += contact.first_name
            if contact.last_name:
                full_name += " " + contact.last_name
            
            # اسم الملف الثابت حسب المطلوب
            display_name = "تسوي سكليف صحتي واتساب"
            
            if full_name.strip():
                vcf_lines.append(f"FN:{display_name}")
                vcf_lines.append(f"N:سكليف صحتي واتساب;تسوي;;;")
            else:
                vcf_lines.append(f"FN:{display_name}")
                vcf_lines.append(f"N:سكليف صحتي واتساب;تسوي;;;")
            
            if contact.phone_number:
                vcf_lines.append(f"TEL;TYPE=CELL:{contact.phone_number}")
            
            if contact.user_id:
                vcf_lines.append(f"X-TELEGRAM-ID:{contact.user_id}")
            
            vcf_lines.append("END:VCARD")
            
            return "\n".join(vcf_lines)
        except Exception as e:
            logger.error(f"خطأ في إنشاء VCF: {str(e)}")
            return None
    
    async def add_ad_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة ملف الإعلان"""
        user_id = update.message.from_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return ConversationHandler.END
        
        ad_type = context.user_data.get('ad_type')
        ad_text = context.user_data.get('ad_text', '')
        
        file_id = None
        file_type = None
        file_name = None
        mime_type = None
        
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = 'photo'
        elif update.message.document:
            file_id = update.message.document.file_id
            file_type = 'document'
            file_name = update.message.document.file_name
            mime_type = update.message.document.mime_type
            
            # التحقق من نوع الملف
            if file_name and file_name.lower().endswith(('.vcf', '.vcard')):
                ad_type = 'contact'
            elif mime_type and 'vcard' in mime_type.lower():
                ad_type = 'contact'
        elif update.message.contact:
            contact = update.message.contact
            vcf_content = self.create_vcf_from_contact(contact)
            
            if vcf_content:
                try:
                    os.makedirs("temp_files/ads", exist_ok=True)
                    
                    # اسم الملف الثابت
                    base_name = "تسوي سكليف صحتي واتساب"
                    file_path = f"temp_files/ads/{base_name}.vcf"
                    
                    # إضافة رقم إذا كان الملف موجوداً
                    counter = 1
                    if os.path.exists(file_path):
                        while os.path.exists(f"temp_files/ads/{base_name}_{counter}.vcf"):
                            counter += 1
                        file_path = f"temp_files/ads/{base_name}_{counter}.vcf"
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(vcf_content)
                    
                    success, message = self.db.add_ad('contact', None, file_path, 'contact', user_id)
                    
                    if success:
                        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_ads")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            "✅ تم إضافة جهة الاتصال بنجاح\n"
                            f"📁 تم حفظها في: {os.path.basename(file_path)}",
                            reply_markup=reply_markup
                        )
                    else:
                        await update.message.reply_text(f"❌ {message}")
                    
                    context.user_data.clear()
                    return ConversationHandler.END
                    
                except Exception as e:
                    logger.error(f"خطأ في حفظ جهة الاتصال: {str(e)}")
                    await update.message.reply_text("❌ حدث خطأ أثناء حفظ جهة الاتصال")
                    return ConversationHandler.END
        
        if file_id:
            try:
                os.makedirs("temp_files/ads", exist_ok=True)
                
                file = await context.bot.get_file(file_id)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                if ad_type == 'contact':
                    base_name = "تسوي سكليف صحتي واتساب"
                    file_path = f"temp_files/ads/{base_name}.vcf"
                    
                    counter = 1
                    if os.path.exists(file_path):
                        while os.path.exists(f"temp_files/ads/{base_name}_{counter}.vcf"):
                            counter += 1
                        file_path = f"temp_files/ads/{base_name}_{counter}.vcf"
                elif file_type == 'photo':
                    file_path = f"temp_files/ads/photo_{timestamp}.jpg"
                else:
                    ext = file_name.split('.')[-1] if file_name else 'bin'
                    file_path = f"temp_files/ads/document_{timestamp}.{ext}"
                
                await file.download_to_drive(file_path)
                
                success, message = self.db.add_ad(ad_type, ad_text, file_path, ad_type, user_id)
                
                if success:
                    keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_ads")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    response_text = f"✅ {message}\n\n"
                    
                    if ad_type == 'photo':
                        response_text += f"🖼️ **الإعلان بالصورة:**\n"
                        response_text += f"📝 النص: {ad_text[:100]}...\n"
                        response_text += f"📁 الملف: {os.path.basename(file_path)}"
                    elif ad_type == 'contact':
                        response_text += f"📞 **جهة اتصال:**\n"
                        response_text += f"📁 الملف: {os.path.basename(file_path)}"
                    
                    await update.message.reply_text(
                        response_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(f"❌ {message}")
                
            except Exception as e:
                logger.error(f"خطأ في حفظ الملف: {str(e)}")
                await update.message.reply_text("❌ حدث خطأ أثناء حفظ الملف")
        
        else:
            await update.message.reply_text("❌ لم يتم التعرف على الملف")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def show_ads(self, query, context):
        """عرض جميع الإعلانات"""
        user_id = query.from_user.id
        ads = self.db.get_ads(user_id)
        
        if not ads:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا توجد إعلانات مضافة!\n"
                "استخدم زر 'إضافة إعلان' لإضافة إعلانات جديدة.",
                reply_markup=reply_markup
            )
            return
        
        text = "📢 **الإعلانات المضافة**\n\n"
        
        keyboard = []
        
        for ad in ads[:15]:  # عرض أول 15 إعلان فقط
            ad_id, ad_type, ad_text, media_path, file_type, added_date, ad_admin_id, is_encoded = ad
            
            type_emoji = {"text": "📝", "photo": "🖼️", "contact": "📞"}
            
            text += f"**#{ad_id}** - {type_emoji.get(ad_type, '📄')} {ad_type}\n"
            
            if ad_type == 'text' and ad_text:
                text += f"📋 {ad_text[:50]}...\n"
            elif ad_type == 'photo' and ad_text:
                text += f"📋 {ad_text[:30]}... + صورة\n"
            elif ad_type == 'contact':
                text += f"📞 جهة اتصال (تسوي سكليف صحتي واتساب.vcf)\n"
            
            text += f"📅 {added_date[:16]}\n"
            text += "─" * 20 + "\n"
            
            keyboard.append([InlineKeyboardButton(f"🗑️ حذف #{ad_id}", callback_data=f"delete_ad_{ad_id}")])
        
        if len(ads) > 15:
            text += f"\n... وعرض {len(ads) - 15} إعلان إضافي"
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث القائمة", callback_data="show_ads"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def delete_ad(self, query, context, ad_id):
        """حذف إعلان"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text(MESSAGES['unauthorized'])
            return
        
        if self.db.delete_ad(ad_id, user_id):
            await query.edit_message_text(f"✅ تم حذف الإعلان #{ad_id} بنجاح")
        else:
            await query.edit_message_text(
                f"❌ فشل حذف الإعلان #{ad_id}\n"
                "قد يكون الإعلان غير موجود أو ليس لديك صلاحية لحذفه."
            )
        
        await self.show_ads(query, context)
    
    async def show_ad_stats(self, query, context):
        """عرض إحصائيات الإعلانات"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MESSAGES['unauthorized'], reply_markup=reply_markup)
            return
        
        stats = self.db.get_statistics(user_id)
        
        text = "📊 **إحصائيات الإعلانات**\n\n"
        
        text += f"📢 **إجمالي الإعلانات:** {stats['ads']}\n\n"
        
        # تعداد الإعلانات حسب النوع
        ads = self.db.get_ads(user_id, decode=False)
        
        type_count = {'text': 0, 'photo': 0, 'contact': 0}
        for ad in ads:
            ad_type = ad[1]
            if ad_type in type_count:
                type_count[ad_type] += 1
        
        text += f"📝 **النصوص:** {type_count['text']}\n"
        text += f"🖼️ **الصور:** {type_count['photo']}\n"
        text += f"📞 **جهات الاتصال:** {type_count['contact']}\n\n"
        
        # آخر الإعلانات المضافة
        if ads:
            text += "📅 **آخر الإعلانات:**\n"
            for ad in ads[:3]:
                ad_id, ad_type, ad_text, media_path, file_type, added_date, ad_admin_id, is_encoded = ad
                type_emoji = {"text": "📝", "photo": "🖼️", "contact": "📞"}
                text += f"   • {type_emoji.get(ad_type, '📄')} #{ad_id} - {added_date[:16]}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="ad_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_ads")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
