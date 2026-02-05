import base64


class TextEncoder:
    """تشفير بسيط مستقر للنصوص (Base64 فقط)"""

    @staticmethod
    def encode_text(text: str) -> str:
        if not text:
            return text

        try:
            return base64.b64encode(text.encode()).decode()
        except:
            return text

    @staticmethod
    def decode_text(encoded_text: str) -> str:
        if not encoded_text:
            return encoded_text

        try:
            return base64.b64decode(encoded_text.encode()).decode()
        except:
            return encoded_text

    @staticmethod
    def create_hash(text: str, length: int = 16) -> str:
        import hashlib

        if not text:
            return ""

        h = hashlib.sha256(text.encode()).hexdigest()
        return h[:length]
