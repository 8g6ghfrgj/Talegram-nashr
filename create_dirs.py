# create_dirs.py
import os
import sys

def create_required_directories():
    """إنشاء جميع المجلدات المطلوبة"""
    
    print("📁 جاري إنشاء المجلدات المطلوبة...")
    
    # المجلدات المطلوبة
    directories = [
        "temp_files/ads",
        "temp_files/group_replies", 
        "temp_files/random_replies",
        "temp_files/logs",
        "temp_files/backups",
        "temp_files/exports"
    ]
    
    created_count = 0
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ تم إنشاء: {directory}")
            created_count += 1
            
            # إنشاء ملف .gitkeep في كل مجلد
            gitkeep_path = os.path.join(directory, ".gitkeep")
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, 'w') as f:
                    f.write("# This file keeps the directory in git\n")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء {directory}: {e}")
    
    # إنشاء ملف README
    readme_content = """# temp_files Directory
# Temporary files for Telegram Bot
"""
    readme_path = "temp_files/README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n🎉 تم إنشاء {created_count} مجلد مطلوب")
    return True

if __name__ == "__main__":
    success = create_required_directories()
    sys.exit(0 if success else 1)
