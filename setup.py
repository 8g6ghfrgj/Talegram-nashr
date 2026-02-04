#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف setup.py للبوت الفعلي - الإصدار المعدل
هذا الملف يستخدم لتثبيت البوت كحزمة Python
"""

import os
import sys
from setuptools import setup, find_packages
from pathlib import Path

# قراءة محتوى README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# التحقق من إصدار Python
if sys.version_info < (3, 11):
    sys.exit('❌ هذا البوت يتطلب Python 3.11 أو أحدث!')

# تعريف حزم البوت
PACKAGES = [
    'database',
    'handlers',
    'managers',
    'utils'
]

# متطلبات التثبيت
INSTALL_REQUIRES = [
    # Telegram Libraries
    'python-telegram-bot[job-queue]==20.7',
    'telethon==1.34.0',
    
    # Utilities
    'python-dotenv==1.0.0',
    'requests==2.31.0',
    'Pillow==10.1.0',
    'APScheduler==3.10.4',
    'cryptography==41.0.7',
    'aiofiles==23.2.1',
    
    # Database (SQLite مدمج في Python، لا حاجة لتثبيته)
    # Additional
    'psutil==5.9.7',      # معلومات النظام
    'colorlog==6.7.0',    # سجلات ملونة
]

# المتطلبات الاختيارية
EXTRAS_REQUIRE = {
    'dev': [
        'pytest==7.4.3',
        'pytest-asyncio==0.21.1',
        'black==23.11.0',
        'flake8==6.1.0',
        'mypy==1.7.1',
    ],
    'docker': [
        'docker==6.1.3',
    ],
    'monitoring': [
        'prometheus-client==0.19.0',
    ]
}

# تعريف نقاط الدخول للبرنامج
ENTRY_POINTS = {
    'console_scripts': [
        'telegram-bot=main:main',
        'bot-cli=cli:main',
    ],
}

def create_directories():
    """إنشاء المجلدات المطلوبة للبوت"""
    directories = [
        "temp_files/ads",
        "temp_files/group_replies",
        "temp_files/random_replies",
        "temp_files/logs",
        "temp_files/backups",
        "temp_files/exports",
        "data",
        "logs",
    ]
    
    created = []
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            created.append(directory)
        except Exception as e:
            print(f"⚠️  تحذير: لم أستطع إنشاء المجلد {directory}: {e}")
    
    return created

def check_environment():
    """التحقق من متغيرات البيئة المطلوبة"""
    required_env_vars = ['BOT_TOKEN']
    missing = []
    
    for var in required_env_vars:
        if var not in os.environ:
            missing.append(var)
    
    if missing:
        print("⚠️  تحذير: متغيرات البيئة التالية غير معينة:")
        for var in missing:
            print(f"   - {var}")
        print("\nيمكنك تعيينها في ملف .env أو في بيئة التشغيل")
    
    return missing

class PostInstallCommand:
    """فئة لتنفيذ أوامر ما بعد التثبيت"""
    def run(self):
        """تنفيذ أوامر ما بعد التثبيت"""
        print("🚀 إعداد البوت الفعلي...")
        
        # إنشاء المجلدات
        created = create_directories()
        if created:
            print(f"✅ تم إنشاء {len(created)} مجلد")
        
        # التحقق من البيئة
        missing = check_environment()
        if missing:
            print("📝 يرجى تعيين متغيرات البيئة قبل تشغيل البوت")
        
        # إنشاء ملف .env.example إذا لم يكن موجوداً
        if not os.path.exists('.env.example'):
            with open('.env.example', 'w', encoding='utf-8') as f:
                f.write("""# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Owner ID (المالك الوحيد)
OWNER_ID=8148890042

# Port for Render/Server
PORT=8080

# Database settings
DATABASE_URL=file:./bot_database.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Delay settings (ثواني)
PUBLISH_DELAY=60
JOIN_DELAY=90

# Security
ENABLE_ENCRYPTION=true
""")
            print("✅ تم إنشاء ملف .env.example")
        
        # إنشاء ملف config.py إذا لم يكن موجوداً
        if not os.path.exists('config.py'):
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write("""import os

# Bot Token - Required
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Owner ID - المالك الوحيد
OWNER_ID = int(os.environ.get('OWNER_ID', 8148890042))

# Database
DB_NAME = os.environ.get('DATABASE_URL', 'bot_database.db')

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', 'logs/bot.log')

# Delay Settings (ثواني)
DELAY_SETTINGS = {
    'publishing': {
        'between_ads': 0.1,
        'between_groups': 0.2,
        'between_cycles': 30,
        'group_publishing_delay': 60,  # تأخير 60 ثانية بين نشر القروبات
    },
    'private_reply': {
        'between_replies': 0.05,
        'between_cycles': 3,
    },
    'group_reply': {
        'between_replies': 0.05,
        'between_cycles': 3,
    },
    'random_reply': {
        'between_replies': 0.05,
        'between_cycles': 3,
    },
    'join_groups': {
        'between_links': 90,
        'between_cycles': 5,
    }
}

# File Settings
FILE_SETTINGS = {
    'contact_filename': "تسوي سكليف صحتي واتساب.vcf",
    'directories': {
        'ads': "temp_files/ads",
        'group_replies': "temp_files/group_replies",
        'random_replies': "temp_files/random_replies",
    }
}

# Conversation States
(
    ADD_ACCOUNT, ADD_AD_TYPE, ADD_AD_TEXT, ADD_AD_MEDIA,
    ADD_GROUP, ADD_PRIVATE_REPLY, ADD_ADMIN,
    ADD_RANDOM_REPLY, ADD_PRIVATE_TEXT, ADD_GROUP_TEXT,
    ADD_GROUP_PHOTO
) = range(11)

# AD Types
AD_TYPES = {
    'text': '📝 نص فقط',
    'photo': '🖼️ صورة مع نص',
    'contact': '📞 جهة اتصال (VCF)'
}

# Group Status
GROUP_STATUS = {
    'pending': '⏳ معلقة',
    'joined': '✅ منضمة',
    'failed': '❌ فشل'
}

def validate_config():
    '''التحقق من صحة الإعدادات'''
    errors = []
    
    if not BOT_TOKEN:
        errors.append("❌ لم يتم تعيين BOT_TOKEN")
    
    if errors:
        for error in errors:
            print(error)
        return False
    
    return True

def print_config():
    '''عرض إعدادات البوت'''
    print("=" * 60)
    print("⚙️  إعدادات البوت الفعلي")
    print("=" * 60)
    print(f"👑 المالك: {OWNER_ID}")
    print(f"📊 تأخير نشر القروبات: {DELAY_SETTINGS['publishing']['group_publishing_delay']} ثانية")
    print(f"📁 اسم ملف جهات الاتصال: {FILE_SETTINGS['contact_filename']}")
    print("=" * 60)
""")
            print("✅ تم إنشاء ملف config.py")
        
        print("\n🎉 تم إعداد البوت بنجاح!")
        print("\n📋 الخطوات التالية:")
        print("1. اضبط BOT_TOKEN في ملف .env أو متغيرات البيئة")
        print("2. قم بتشغيل البوت: python main.py")
        print("3. ابدأ باستخدام /start في Telegram")

# إعداد البنية الرئيسية
setup(
    # المعلومات الأساسية
    name="telegram-auto-bot",
    version="2.0.0",
    author="Telegram Bot Team",
    author_email="support@example.com",
    description="Telegram Auto Publishing Bot - Maximum Speed with 60s Delay",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # الروابط
    url="https://github.com/yourusername/telegram-auto-bot",
    project_urls={
        "Documentation": "https://github.com/yourusername/telegram-auto-bot/wiki",
        "Source Code": "https://github.com/yourusername/telegram-auto-bot",
        "Bug Tracker": "https://github.com/yourusername/telegram-auto-bot/issues",
    },
    
    # التصنيفات
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: Arabic",
    ],
    
    # الكلمات الدلالية
    keywords=[
        "telegram",
        "bot",
        "auto-posting",
        "arabic",
        "marketing",
        "automation",
        "publishing",
        "telegram-bot",
    ],
    
    # الرخصة
    license="MIT",
    
    # الحزم
    packages=find_packages(include=['*', 'database.*', 'handlers.*', 'managers.*', 'utils.*']),
    include_package_data=True,
    zip_safe=False,
    
    # المتطلبات
    python_requires=">=3.11",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    
    # نقاط الدخول
    entry_points=ENTRY_POINTS,
    
    # بيانات الحزمة
    package_data={
        '': [
            '*.md',
            '*.txt',
            '*.toml',
            '*.yaml',
            '*.yml',
        ],
        'database': ['*.py'],
        'handlers': ['*.py'],
        'managers': ['*.py'],
        'utils': ['*.py'],
    },
    
    # الأوامر المخصصة
    cmdclass={
        'install': PostInstallCommand,
    },
    
    # منع التثبيت في بعض الحالات
    platforms=["any"],
    
    # المعلومات الإضافية
    maintainer="Bot Maintainer",
    maintainer_email="maintainer@example.com",
    
    # الدعم
    provides=["telegram_auto_bot"],
    obsoletes=["old-telegram-bot"],
)

if __name__ == "__main__":
    # عند تشغيل الملف مباشرة
    print("🔧 ملف إعداد البوت الفعلي")
    print("=" * 50)
    
    # التحقق من Python
    if sys.version_info < (3, 11):
        print("❌ خطأ: يتطلب Python 3.11 أو أحدث!")
        sys.exit(1)
    
    # إنشاء المجلدات
    created = create_directories()
    print(f"📁 تم إنشاء {len(created)} مجلد مؤقت")
    
    # التحقق من المتطلبات
    try:
        import sqlite3
        print("✅ sqlite3: متوفر (مدمج في Python)")
    except ImportError:
        print("❌ sqlite3: غير متوفر - مشكلة في Python")
    
    print("\n📦 لتثبيت البوت:")
    print("1. pip install -e .  (للتطوير)")
    print("2. pip install .     (للتثبيت العادي)")
    print("\n🚀 لتشغيل البوت:")
    print("python main.py")
    print("=" * 50)
