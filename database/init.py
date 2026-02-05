"""
حزمة قاعدة البيانات للبوت

تحتوي على:

1. BotDatabase : إدارة قاعدة البيانات بالكامل
2. TextEncoder : طبقة توافق (بدون تشفير فعلي)
"""

from .database import BotDatabase
from .text_encoder import TextEncoder


__all__ = [
    "BotDatabase",
    "TextEncoder"
]


__version__ = "1.0.0"
