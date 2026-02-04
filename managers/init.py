"""
حزمة مديري العمليات للبوت الفعلي

هذه الحزمة تحتوي على:
1. TelegramBotManager: المدير الرئيسي لعمليات تليجرام
2. TaskManager: مدير المهام الخلفية
"""

from .telegram_manager import TelegramBotManager

__all__ = ['TelegramBotManager']
__version__ = '1.0.0'
