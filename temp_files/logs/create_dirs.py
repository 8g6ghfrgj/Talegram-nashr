import os


def create_required_directories():
    """إنشاء جميع المجلدات المطلوبة للبوت"""

    directories = [
        "temp_files/ads",
        "temp_files/group_replies",
        "temp_files/random_replies",
        "temp_files/logs",
        "temp_files/backups",
        "temp_files/exports"
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ {directory}")
        except Exception as e:
            print(f"❌ فشل إنشاء {directory}: {e}")


if __name__ == "__main__":
    print("📁 إنشاء المجلدات...")
    create_required_directories()
    print("✅ تم الانتهاء")
