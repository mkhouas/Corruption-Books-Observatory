#!/usr/bin/env python3
"""
🤖 السكريبت الرئيسي – مرصد كتب الفساد
يُشغَّل يوميًا عبر GitHub Actions

المراحل:
1. جلب الكتب من APIs متعددة
2. دمج الإضافات اليدوية
3. تصفية (خيال، منتهي، مكرر، غير ذي صلة)
4. تحديث قاعدة البيانات
5. توليد README.md و index.html
"""

import json
import os
import sys
from datetime import datetime

# إضافة المجلد الحالي إلى المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PATHS, TODAY
from fetcher import BooksFetcher
from filter_engine import FilterEngine
from generate_readme import generate_readme
from generate_html import generate_html


def load_json(filepath: str, default=None):
    """تحميل ملف JSON"""
    if default is None:
        default = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(filepath: str, data):
    """حفظ ملف JSON"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 60)
    print(f"📚 مرصد كتب الفساد – تحديث يومي")
    print(f"📅 التاريخ: {TODAY.isoformat()}")
    print(f"⏰ الوقت: {datetime.utcnow().strftime('%H:%M:%S')} UTC")
    print("=" * 60)
    
    force_refresh = os.environ.get("FORCE_REFRESH", "false") == "true"
    
    # ─── 1. تحميل قاعدة البيانات الحالية ───
    print("\n📂 تحميل قاعدة البيانات الحالية...")
    db = load_json(PATHS["books_db"], {"books": [], "metadata": {}})
    existing_books = db.get("books", [])
    print(f"  📊 الكتب الحالية: {len(existing_books)}")
    
    # ─── 2. جلب كتب جديدة من APIs ───
    print("\n🔌 جلب الكتب من المصادر الخارجية...")
    fetcher = BooksFetcher()
    
    try:
        raw_books = fetcher.fetch_all_sources()
    except Exception as e:
        print(f"  ❌ خطأ في الجلب: {e}")
        raw_books = []
    
    # ─── 3. تحميل الإضافات اليدوية ───
    print("\n📝 تحميل الإضافات اليدوية...")
    manual_entries = load_json(PATHS["manual_entries"], [])
    if isinstance(manual_entries, dict):
        manual_entries = manual_entries.get("books", [])
    print(f"  📊 إضافات يدوية: {len(manual_entries)}")
    
    # دمج اليدوي مع الحالي
    all_existing = existing_books + manual_entries
    
    # ─── 4. التصفية والمعالجة ───
    print("\n🔍 بدء التصفية والمعالجة...")
    engine = FilterEngine()
    
    if force_refresh:
        print("  ⚡ وضع التحديث الكامل – إعادة معالجة شاملة")
        filtered_books = engine.process(raw_books, [])
        # إضافة اليدوي بعد التصفية
        for entry in manual_entries:
            if not engine.is_fiction(entry) and not engine.is_expired(entry):
                filtered_books.append(entry)
    else:
        filtered_books = engine.process(raw_books, all_existing)
    
    engine.print_stats()
    
    # ─── 5. تحديث قاعدة البيانات ───
    print("\n💾 حفظ قاعدة البيانات...")
    db = {
        "metadata": {
            "name": "Corruption Books Observatory",
            "last_updated": TODAY.isoformat(),
            "update_time_utc": datetime.utcnow().isoformat(),
            "total_books": len(filtered_books),
            "validity_months": 24,
            "sources": ["google_books", "open_library", "crossref", "manual"],
            "stats": engine.stats,
        },
        "books": filtered_books,
    }
    save_json(PATHS["books_db"], db)
    print(f"  ✅ تم حفظ {len(filtered_books)} كتاب")
    
    # ─── 6. توليد README.md ───
    print("\n📝 توليد README.md...")
    readme_content = generate_readme(filtered_books, engine.stats)
    with open(PATHS["readme"], "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"  ✅ تم توليد README.md ({len(readme_content)} حرف)")
    
    # ─── 7. توليد index.html ───
    print("\n🌐 توليد index.html...")
    html_content = generate_html(filtered_books, engine.stats)
    with open(PATHS["index_html"], "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  ✅ تم توليد index.html ({len(html_content)} حرف)")
    
    # ─── 8. ملخص نهائي ───
    print("\n" + "=" * 60)
    print("✅ اكتمل التحديث اليومي بنجاح!")
    print(f"  📚 الكتب النشطة: {len(filtered_books)}")
    print(f"  🆕 كتب جديدة: {engine.stats['new_books']}")
    print(f"  📦 كتب مؤرشفة: {engine.stats['archived']}")
    print(f"  📅 نافذة الصلاحية: {engine.stats.get('cutoff', 'N/A')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
