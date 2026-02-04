"""
سكريبت لتنظيف الملفات المؤقتة القديمة
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
import shutil

def cleanup_temp_files(days_old: int = 7, dry_run: bool = False):
    """
    تنظيف الملفات المؤقتة القديمة
    
    Args:
        days_old: عدد الأيام (الملفات الأقدم من هذا سيتم حذفها)
        dry_run: وضع الاختبار (لا يحذف أي ملفات)
    """
    print(f"🧹 بدء تنظيف الملفات الأقدم من {days_old} يوم...")
    
    temp_dirs = [
        "temp_files/ads",
        "temp_files/group_replies", 
        "temp_files/random_replies",
        "temp_files/logs"
    ]
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    total_deleted = 0
    total_size = 0
    
    for directory in temp_dirs:
        if not os.path.exists(directory):
            print(f"⚠️ المجلد غير موجود: {directory}")
            continue
        
        print(f"\n📂 فحص: {directory}")
        dir_deleted = 0
        dir_size = 0
        
        for filename in os.listdir(directory):
            # تخطي ملفات النظام
            if filename.startswith('.') or filename == '.gitkeep':
                continue
            
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    file_size = os.path.getsize(file_path)
                    
                    if file_time < cutoff_time:
                        dir_deleted += 1
                        dir_size += file_size
                        
                        if dry_run:
                            print(f"   🔍 سيتم حذف: {filename} ({file_time.date()})")
                        else:
                            os.remove(file_path)
                            print(f"   🗑️ تم حذف: {filename} ({file_time.date()})")
                            
                except Exception as e:
                    print(f"   ❌ خطأ في معالجة {filename}: {e}")
        
        total_deleted += dir_deleted
        total_size += dir_size
        
        if dir_deleted > 0:
            size_mb = dir_size / (1024 * 1024)
            print(f"   📊 حُذف {dir_deleted} ملف ({size_mb:.2f} MB)")
        else:
            print("   ✅ لا توجد ملفات قديمة")
    
    # تنظيف المجلدات الفارغة (عدا المجلدات الرئيسية)
    if not dry_run:
        for directory in temp_dirs:
            try:
                # احصل على جميع الملفات والمجلدات (عدا .gitkeep)
                items = [item for item in os.listdir(directory) 
                        if item != '.gitkeep' and not item.startswith('.')]
                
                if not items:  # إذا كان المجلد فارغاً
                    # لا تحذف المجلدات الرئيسية
                    if directory.count('/') > 1:  # مجلدات فرعية فقط
                        shutil.rmtree(directory)
                        print(f"🗑️ تم حذف المجلد الفارغ: {directory}")
            except Exception as e:
                print(f"❌ خطأ في حذف المجلد الفارغ {directory}: {e}")
    
    print(f"\n{'='*50}")
    
    if dry_run:
        print(f"🔍 وضع الاختبار: سيتم حذف {total_deleted} ملف ({total_size/1024/1024:.2f} MB)")
        print("⚠️ لم يتم حذف أي ملفات فعلياً")
    else:
        if total_deleted > 0:
            print(f"✅ تم تنظيف {total_deleted} ملف قديم ({total_size/1024/1024:.2f} MB)")
        else:
            print("✅ لا توجد ملفات قديمة للتنظيف")
    
    print("=" * 50)

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description='تنظيف الملفات المؤقتة القديمة')
    parser.add_argument('--days', type=int, default=7, 
                       help='عدد الأيام (الملفات الأقدم من هذا سيتم حذفها)')
    parser.add_argument('--dry-run', action='store_true',
                       help='وضع الاختبار (لا يحذف أي ملفات)')
    
    args = parser.parse_args()
    
    print("🧹 منظف الملفات المؤقتة للبوت الفعلي")
    print("=" * 50)
    
    try:
        cleanup_temp_files(days_old=args.days, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف العملية بواسطة المستخدم")
        sys.exit(0)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
