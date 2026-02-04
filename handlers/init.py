"""
حزمة معالجات البوت الفعلي

هذه الحزمة تحتوي على جميع معالجات الأوامر والمحادثات للبوت.
"""

from .account_handlers import AccountHandlers
from .ad_handlers import AdHandlers
from .group_handlers import GroupHandlers
from .reply_handlers import ReplyHandlers
from .admin_handlers import AdminHandlers
from .conversation_handlers import ConversationHandlers

__all__ = [
    'AccountHandlers',
    'AdHandlers',
    'GroupHandlers', 
    'ReplyHandlers',
    'AdminHandlers',
    'ConversationHandlers'
]

__version__ = '1.0.0'
