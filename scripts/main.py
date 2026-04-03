
---

## 7️⃣ `scripts/main.py` (محدّث: مرحلة حل الأغلفة)

```python
#!/usr/bin/env python3
"""
🤖 السكريبت الرئيسي – مع مرحلة حل الأغلفة
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PATHS, TODAY, COVER_CONFIG
from fetcher import BooksFetcher
from filter_engine import FilterEngine
from cover_resolver import CoverResolver
from generate_readme import generate_readme
from generate_html import generate_html


def load_json(fp, default=None):
    if default is None:
        default = {}
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(fp, data):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 60)
    print("📚 مرصد كتب الفساد – تحديث يومي")
    print(f"📅 {TODAY.isoformat()} | ⏰ {datetime.utcnow().strftime('%H:%M:%S')} UTC")
    print("=" * 60)

    force = os.environ.get("FORCE_REFRESH", "false") == "true"

    # ─── 1. تحميل البيانات الحالية ───
    print("\n📂 تحميل قاعدة البيانات...")
    db = load_json(PATHS["books_db"], {"books": [], "metadata": {}})
    existing = db.get("books", [])
    print(f"  📊 حالياً: {len(existing)} كتاب")

    # ─── 2. جلب كتب جديدة ───
    print("\n🔌 جلب من المصادر...")
    fetcher = BooksFetcher()
    try:
        raw = fetcher.fetch_all_sources()
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        raw = []

    # ─── 3. إضافات يدوية ───
    print("\n📝 إضافات يدوية...")
    manual = load_json(PATHS["manual_entries"], [])
    if isinstance(manual, dict):
        manual = manual.get("books", [])
    print(f"  📊 يدوية: {len(manual)}")

    all_existing = existing + manual

    # ─── 4. التصفية ───
    print("\n🔍 التصفية...")
    engine = FilterEngine()
    if force:
        filtered = engine.process(raw, [])
        for entry in manual:
            if not engine.is_fiction(entry) and not engine.is_expired(entry):
                filtered.append(entry)
    else:
        filtered = engine.process(raw, all_existing)
    engine.print_stats()

    # ─── 5. 🆕 حل الأغلفة ───
    print("\n🖼️ البحث عن أغلفة الكتب...")
    resolver = CoverResolver()

    for book in filtered:
        cover = book.get("cover_url", "")
        # البحث فقط إذا لم يكن هناك غلاف أو كان placeholder
        if not cover or "placeholder" in cover:
            new_cover, new_info = resolver.resolve(book)
            book["cover_url"] = new_cover
            if new_info and not book.get("info_url"):
                book["info_url"] = new_info
        # التأكد من وجود info_url
        if not book.get("info_url"):
            book["info_url"] = book.get("link", "")

    resolver.print_stats()

    # تحديث إحصائيات الأغلفة في محرك التصفية
    engine.stats["covers_found"] = resolver.stats["resolved"] + resolver.stats["cached"]
    engine.stats["covers_missing"] = resolver.stats["failed"]

    # ─── 6. حفظ ───
    print("\n💾 حفظ...")
    db = {
        "metadata": {
            "name": "Corruption Books Observatory",
            "last_updated": TODAY.isoformat(),
            "update_time_utc": datetime.utcnow().isoformat(),
            "total_books": len(filtered),
            "validity_months": 24,
            "sources": ["google_books", "open_library", "crossref", "manual"],
            "stats": engine.stats,
            "cover_stats": resolver.stats,
        },
        "books": filtered,
    }
    save_json(PATHS["books_db"], db)

    # ─── 7. README.md ───
    print("\n📝 توليد README.md...")
    readme = generate_readme(filtered, engine.stats)
    with open(PATHS["readme"], "w", encoding="utf-8") as f:
        f.write(readme)

    # ─── 8. index.html ───
    print("\n🌐 توليد index.html...")
    html = generate_html(filtered, engine.stats)
    with open(PATHS["index_html"], "w", encoding="utf-8") as f:
        f.write(html)

    # ─── 9. ملخص ───
    print(f"\n{'='*60}")
    print("✅ اكتمل!")
    print(f"  📚 كتب: {len(filtered)}")
    print(f"  🆕 جديدة: {engine.stats['new_books']}")
    print(f"  📦 مؤرشفة: {engine.stats['archived']}")
    print(f"  🖼️ أغلفة: {resolver.stats['resolved']}/{resolver.stats['resolved']+resolver.stats['failed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
