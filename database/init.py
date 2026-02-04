"""
حزمة قاعدة البيانات للبوت الفعلي

هذه الحزمة تحتوي على:
1. BotDatabase: الفئة الرئيسية لإدارة قاعدة البيانات
2. TextEncoder: فئة لتشفير وفك تشفير النصوص
"""

from .database import BotDatabase
from .text_encoder import TextEncoder

__all__ = ['BotDatabase', 'TextEncoder']
__version__ = '1.0.0'
