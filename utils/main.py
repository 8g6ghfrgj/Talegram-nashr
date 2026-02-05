import os
import sys

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers import Helpers


def test_helpers():
    print("🧪 اختبار أدوات المساعدة\n")

    # نص عشوائي
    random_text = Helpers.generate_random_string(20)
    print(f"📝 نص عشوائي: {random_text}")

    # روابط للاختبار
    test_links = [
        "https://t.me/testchannel",
        "t.me/testgroup",
        "@username123",
        "+invitecode123",
        "invalid_link"
    ]

    print("\n🔗 اختبار الروابط:")
    for link in test_links:
        valid = Helpers.validate_telegram_link(link)
        print(f"{link} -> {'✅ صالح' if valid else '❌ غير صالح'}")

    # استخراج روابط من نص
    text = "انضم هنا https://t.me/test1 و @test2 و رابط خاطئ abc"
    extracted = Helpers.extract_links(text)

    print("\n📥 الروابط المستخرجة:")
    for link in extracted:
        print(f" - {link}")

    # تنظيف اسم ملف
    dirty = 'file<>:"/\\|?*name.txt'
    clean = Helpers.clean_filename(dirty)

    print(f"\n🧹 تنظيف اسم ملف:")
    print(f"{dirty} -> {clean}")

    # تقصير نص
    long_text = "هذا نص طويل جداً " * 10
    short = Helpers.truncate_text(long_text, 50)

    print(f"\n✂️ تقصير النص:")
    print(short)

    # فحص session string
    fake_session = "A" * 120
    print(f"\n🔐 Session صالح؟ {Helpers.is_valid_session_string(fake_session)}")

    print("\n✅ انتهت جميع الاختبارات بنجاح")


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 بدء اختبار Helpers")
    print("=" * 50)

    try:
        test_helpers()
        print("\n🎉 كل شيء يعمل بشكل سليم")
    except Exception as e:
        print(f"\n❌ فشل الاختبار: {e}")
        import traceback
        traceback.print_exc()
