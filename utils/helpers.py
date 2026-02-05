import os
import re
import random
import string
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Helpers:
    """أدوات مساعدة بسيطة للبوت"""

    @staticmethod
    def validate_telegram_link(link: str) -> bool:
        """التحقق من صحة رابط تليجرام"""

        patterns = [
            r'^https?://t\.me/[a-zA-Z0-9_]+$',
            r'^https?://t\.me/\+[a-zA-Z0-9_-]+$',
            r'^t\.me/[a-zA-Z0-9_]+$',
            r'^\+[a-zA-Z0-9_-]+$',
            r'^@[a-zA-Z0-9_]+$'
        ]

        for pattern in patterns:
            if re.match(pattern, link):
                return True

        return False

    @staticmethod
    def extract_links(text: str):
        """استخراج روابط تليجرام من نص"""

        pattern = r'(https?://t\.me/[^\s]+|t\.me/[^\s]+|\+[a-zA-Z0-9_-]+|@[a-zA-Z0-9_]+)'
        found = re.findall(pattern, text)

        return [link for link in found if Helpers.validate_telegram_link(link)]

    @staticmethod
    def clean_filename(filename: str) -> str:
        """تنظيف اسم الملف"""

        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)

        if len(cleaned) > 100:
            name, ext = os.path.splitext(cleaned)
            cleaned = name[:90] + ext

        return cleaned

    @staticmethod
    def generate_unique_filename(filename: str, directory: str) -> str:
        """إنشاء اسم ملف غير مكرر"""

        filename = Helpers.clean_filename(filename)
        path = os.path.join(directory, filename)

        if not os.path.exists(path):
            return filename

        name, ext = os.path.splitext(filename)
        counter = 1

        while os.path.exists(os.path.join(directory, f"{name}_{counter}{ext}")):
            counter += 1

        return f"{name}_{counter}{ext}"

    @staticmethod
    def create_directories(dirs):
        """إنشاء مجلدات"""

        for d in dirs:
            try:
                os.makedirs(d, exist_ok=True)
                logger.info(f"📁 {d}")
            except Exception as e:
                logger.error(f"❌ فشل إنشاء {d}: {e}")

    @staticmethod
    def cleanup_old_files(directory: str, days: int = 7):
        """حذف الملفات القديمة"""

        if not os.path.exists(directory):
            return

        cutoff = datetime.now() - timedelta(days=days)

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if not os.path.isfile(file_path):
                continue

            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                if file_time < cutoff:
                    os.remove(file_path)
                    logger.debug(f"🗑️ حذف: {filename}")

            except Exception as e:
                logger.error(f"❌ فشل حذف {filename}: {e}")

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """إنشاء نص عشوائي"""

        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def truncate_text(text: str, max_length: int = 100):
        """تقصير النص الطويل"""

        if len(text) <= max_length:
            return text

        return text[:max_length] + "..."

    @staticmethod
    def is_valid_session_string(session: str) -> bool:
        """تحقق بسيط من session string"""

        if not session:
            return False

        return len(session) > 100
