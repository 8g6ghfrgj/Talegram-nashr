import logging

logger = logging.getLogger(__name__)


class TextEncoder:
    """
    نسخة مبسطة بدون أي تشفير

    الهدف فقط الحفاظ على التوافق مع الكود القديم
    بدون كسر أي شيء أو تعقيد
    """

    @staticmethod
    def encode_text(text):
        return text

    @staticmethod
    def decode_text(text):
        return text

    @staticmethod
    def create_hash(text, length=16):
        if not text:
            return ""
        return text[:length]

    @staticmethod
    def encrypt_file(file_path, output_path=None):
        return False, "Encryption disabled"

    @staticmethod
    def decrypt_file(file_path, output_path=None):
        return False, "Decryption disabled"
