import base64
import random
import hashlib
import logging
from typing import Optional, Tuple
import os

logger = logging.getLogger(__name__)

class TextEncoder:
    """
    فئة متقدمة لتشفير وفك تشفير النصوص باستخدام تقنيات متعددة
    مع دعم التوافق مع الإصدارات السابقة
    """
    
    # مفتاح تشفير افتراضي (يمكن تغييره)
    DEFAULT_KEY = "telegram_bot_encoder_v2"
    
    @staticmethod
    def encode_text(text: str, use_advanced: bool = True) -> str:
        """
        تشفير النص باستخدام تقنيات متعددة
        
        Args:
            text: النص المراد تشفيره
            use_advanced: استخدام التشفير المتقدم (المفترض) أو البسيط
            
        Returns:
            نص مشفر
        """
        if not text or not isinstance(text, str):
            return text
        
        try:
            if use_advanced:
                return TextEncoder._encode_advanced(text)
            else:
                return TextEncoder._encode_simple(text)
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشفير النص: {str(e)}")
            return text
    
    @staticmethod
    def _encode_advanced(text: str) -> str:
        """تشفير متقدم باستخدام تقنيات متعددة"""
        # 1. إضافة ملح عشوائي
        salt = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
        
        # 2. XOR تشفير مع مفتاح عشوائي
        key = random.randint(1, 255)
        xor_encoded = ''.join(chr(ord(c) ^ key) for c in text)
        
        # 3. Reverse النص
        reversed_text = text[::-1]
        
        # 4. Base64 تشفير
        base64_encoded = base64.b64encode(text.encode()).decode()
        
        # 5. Rot13 للنص العكسي
        rot13_reversed = ''
        for char in reversed_text:
            if 'a' <= char <= 'z':
                rot13_reversed += chr((ord(char) - ord('a') + 13) % 26 + ord('a'))
            elif 'A' <= char <= 'Z':
                rot13_reversed += chr((ord(char) - ord('A') + 13) % 26 + ord('A'))
            elif 'أ' <= char <= 'ي':
                rot13_reversed += chr((ord(char) - ord('أ') + 13) % 28 + ord('أ'))
            else:
                rot13_reversed += char
        
        # 6. جمع كل التشفيرات
        combined = f"ADV2:B64:{base64_encoded}|XOR:{xor_encoded}|REV:{rot13_reversed}|KEY:{key}|SALT:{salt}"
        
        # 7. تشفير نهائي
        final_encoded = base64.b64encode(combined.encode()).decode()
        
        # 8. إضافة checksum للتحقق
        checksum = TextEncoder._calculate_checksum(final_encoded)
        
        return f"ENC_V2-{final_encoded}-{checksum}"
    
    @staticmethod
    def _encode_simple(text: str) -> str:
        """تشفير بسيط (للتوافق مع الإصدارات القديمة)"""
        # تشفير Base64 بسيط
        encoded = base64.b64encode(text.encode()).decode()
        
        # Reverse النص
        reversed_text = text[::-1]
        
        # XOR مع مفتاح عشوائي
        key = random.randint(1, 255)
        xor_encoded = ''.join(chr(ord(c) ^ key) for c in text)
        
        combined = f"B64:{encoded}|REV:{reversed_text}|XOR:{xor_encoded}|KEY:{key}"
        final_encoded = base64.b64encode(combined.encode()).decode()
        
        return final_encoded
    
    @staticmethod
    def decode_text(encoded_text: str) -> str:
        """
        فك تشفير النص المشفر
        
        Args:
            encoded_text: النص المشفر
            
        Returns:
            النص الأصلي
        """
        if not encoded_text or not isinstance(encoded_text, str):
            return encoded_text
        
        try:
            # محاولة فك تشفير الإصدار المتقدم أولاً
            if encoded_text.startswith("ENC_V2-"):
                return TextEncoder._decode_advanced_v2(encoded_text)
            
            # محاولة فك تشفير الإصدار البسيط
            return TextEncoder._decode_simple(encoded_text)
            
        except Exception as e:
            logger.error(f"❌ خطأ في فك تشفير النص: {str(e)}")
            return encoded_text
    
    @staticmethod
    def _decode_advanced_v2(encoded_text: str) -> str:
        """فك تشفير الإصدار المتقدم V2"""
        # إزالة البادئة والنهاية
        if not encoded_text.startswith("ENC_V2-") or encoded_text.count('-') != 2:
            raise ValueError("تنسيق النص المشفر غير صحيح")
        
        parts = encoded_text.split('-')
        main_encoded = parts[1]
        expected_checksum = parts[2]
        
        # التحقق من checksum
        actual_checksum = TextEncoder._calculate_checksum(main_encoded)
        if actual_checksum != expected_checksum:
            logger.warning("⚠️ تحذير: checksum غير متطابق - قد يكون النص تالفاً")
        
        # فك Base64 الأول
        decoded = base64.b64decode(main_encoded.encode()).decode()
        
        # التحقق من البادئة
        if not decoded.startswith("ADV2:"):
            raise ValueError("تنسيق النص المشفر غير صحيح")
        
        # إزالة البادئة
        decoded = decoded[5:]
        
        # استخراج الأجزاء
        parts_dict = {}
        for part in decoded.split('|'):
            if ':' in part:
                key, value = part.split(':', 1)
                parts_dict[key] = value
        
        # محاولة فك التشفير من XOR أولاً (الأكثر أماناً)
        if 'XOR' in parts_dict and 'KEY' in parts_dict:
            try:
                key = int(parts_dict['KEY'])
                xor_decoded = ''.join(chr(ord(c) ^ key) for c in parts_dict['XOR'])
                return xor_decoded
            except:
                pass
        
        # محاولة فك Rot13 للنص العكسي
        if 'REV' in parts_dict:
            try:
                rot13_text = parts_dict['REV']
                original_reversed = ''
                for char in rot13_text:
                    if 'a' <= char <= 'z':
                        original_reversed += chr((ord(char) - ord('a') - 13) % 26 + ord('a'))
                    elif 'A' <= char <= 'Z':
                        original_reversed += chr((ord(char) - ord('A') - 13) % 26 + ord('A'))
                    elif 'أ' <= char <= 'ي':
                        original_reversed += chr((ord(char) - ord('أ') - 13) % 28 + ord('أ'))
                    else:
                        original_reversed += char
                
                return original_reversed[::-1]
            except:
                pass
        
        # استخدام Base64 الأساسي
        if 'B64' in parts_dict:
            try:
                return base64.b64decode(parts_dict['B64']).decode()
            except:
                pass
        
        raise ValueError("فشل فك تشفير النص")
    
    @staticmethod
    def _decode_simple(encoded_text: str) -> str:
        """فك تشفير الإصدار البسيط"""
        try:
            decoded = base64.b64decode(encoded_text.encode()).decode()
            
            parts = {}
            for part in decoded.split('|'):
                if ':' in part:
                    key, value = part.split(':', 1)
                    parts[key] = value
            
            if 'XOR' in parts and 'KEY' in parts:
                key = int(parts['KEY'])
                xor_decoded = ''.join(chr(ord(c) ^ key) for c in parts['XOR'])
                return xor_decoded
            
            if 'B64' in parts:
                return base64.b64decode(parts['B64']).decode()
            
            return decoded
        except:
            return encoded_text
    
    @staticmethod
    def _calculate_checksum(text: str) -> str:
        """حساب checksum للنص"""
        hash_object = hashlib.md5(text.encode())
        return hash_object.hexdigest()[:8]
    
    @staticmethod
    def create_hash(text: str, length: int = 16) -> str:
        """
        إنشاء هاش للنص
        
        Args:
            text: النص المراد عمل هاش له
            length: طول الهاش المطلوب
            
        Returns:
            هاش النص
        """
        if not text:
            return ''
        
        # إنشاء هاش SHA256
        hash_object = hashlib.sha256(text.encode())
        hex_dig = hash_object.hexdigest()
        
        # تقصير الهاش للطول المطلوب
        return hex_dig[:length]
    
    @staticmethod
    def encrypt_file(file_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        تشفير ملف
        
        Args:
            file_path: مسار الملف المراد تشفيره
            output_path: مسار الملف الناتج (اختياري)
            
        Returns:
            (نجاح العملية، مسار الملف الناتج أو رسالة الخطأ)
        """
        try:
            if not os.path.exists(file_path):
                return False, "الملف غير موجود"
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # تشفير المحتوى باستخدام Base64
            encoded_content = base64.b64encode(content)
            
            output = output_path or file_path + '.enc'
            with open(output, 'wb') as f:
                f.write(encoded_content)
            
            logger.info(f"✅ تم تشفير الملف: {file_path} -> {output}")
            return True, output
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشفير الملف {file_path}: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def decrypt_file(file_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        فك تشفير ملف
        
        Args:
            file_path: مسار الملف المشفر
            output_path: مسار الملف الناتج (اختياري)
            
        Returns:
            (نجاح العملية، مسار الملف الناتج أو رسالة الخطأ)
        """
        try:
            if not os.path.exists(file_path):
                return False, "الملف غير موجود"
            
            with open(file_path, 'rb') as f:
                encoded_content = f.read()
            
            # فك تشفير المحتوى
            content = base64.b64decode(encoded_content)
            
            output = output_path or file_path.replace('.enc', '')
            with open(output, 'wb') as f:
                f.write(content)
            
            logger.info(f"✅ تم فك تشفير الملف: {file_path} -> {output}")
            return True, output
            
        except Exception as e:
            logger.error(f"❌ خطأ في فك تشفير الملف {file_path}: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def compress_text(text: str) -> str:
        """
        ضغط النص (تقليل حجمه)
        
        Args:
            text: النص المراد ضغطه
            
        Returns:
            نص مضغوط
        """
        if not text:
            return text
        
        try:
            # استخدام Base64 للضغط (ليس فعلياً لكنه يغير التنسيق)
            compressed = base64.b64encode(text.encode()).decode()
            
            # إضافة علامة الضغط
            return f"COMP:{compressed}"
        except:
            return text
    
    @staticmethod
    def decompress_text(compressed_text: str) -> str:
        """
        فك ضغط النص
        
        Args:
            compressed_text: النص المضغوط
            
        Returns:
            النص الأصلي
        """
        if not compressed_text or not compressed_text.startswith("COMP:"):
            return compressed_text
        
        try:
            compressed = compressed_text[5:]  # إزالة "COMP:"
            return base64.b64decode(compressed).decode()
        except:
            return compressed_text
    
    @staticmethod
    def generate_session_string() -> str:
        """
        إنشاء كود جلسة عشوائي (للاختبار فقط)
        
        Returns:
            كود جلسة عشوائي
        """
        import string
        
        # إنشاء نص عشوائي طويل
        length = random.randint(150, 200)
        characters = string.ascii_letters + string.digits + "+/="
        
        session_string = ''.join(random.choices(characters, k=length))
        
        # إضافة بادئة لجعلها تبدو مثل session string حقيقي
        prefixes = ["1", "2", "3"]
        prefix = random.choice(prefixes)
        
        return f"{prefix}{session_string}"
