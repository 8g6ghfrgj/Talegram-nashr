#!/usr/bin/env python3
import os
import sys
import subprocess

def setup_project():
    """إعداد المشروع"""
    print("⚙️  جاري إعداد مشروع البوت...")
    
    # إنشاء المجلدات
    folders = [
        "temp_files/ads",
        "temp_files/group_replies",
        "temp_files/random_replies",
        "database",
        "handlers",
        "managers",
        "utils"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ تم إنشاء المجلد: {folder}")
    
    # إنشاء ملف __init__.py في المجلدات
    init_files = [
        "database/__init__.py",
        "handlers/__init__.py",
        "managers/__init__.py",
        "utils/__init__.py"
    ]
    
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write('')
        print(f"✅ تم إنشاء: {init_file}")
    
    # تثبيت المتطلبات
    print("📦 جاري تثبيت المتطلبات...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ تم تثبيت المتطلبات بنجاح!")
    except subprocess.CalledProcessError:
        print("❌ فشل تثبيت المتطلبات")
        sys.exit(1)
    
    # إنشاء ملف قاعدة البيانات
    from database.database import BotDatabase
    db = BotDatabase()
    print("✅ تم إنشاء قاعدة البيانات")
    
    # التحقق من التوكن
    from config import validate_config
    if validate_config():
        print("✅ جميع الإعدادات صحيحة!")
    else:
        print("❌ هناك مشكلة في الإعدادات")
        sys.exit(1)
    
    print("\n🎉 تم إعداد المشروع بنجاح!")
    print("🚀 لتشغيل البوت: python main.py")

if __name__ == "__main__":
    setup_project()
