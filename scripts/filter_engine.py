"""
🔍 محرك التصفية – مع حفظ بيانات الأغلفة
"""

import json
import os
import re
import hashlib
from datetime import datetime
from typing import List, Tuple
from config import (
    FICTION_EXCLUDE_KEYWORDS, FICTION_EXCLUDE_CATEGORIES,
    REGIONS, CUTOFF_DATE, TODAY, MIN_PAGES, PATHS, BOOK_TYPES
)
from fetcher import BookEntry, parse_date


class FilterEngine:
    def __init__(self):
        self.stats = {
            "total_raw": 0, "removed_fiction": 0, "removed_expired": 0,
            "removed_duplicate": 0, "removed_short": 0,
            "removed_irrelevant": 0, "final_count": 0,
            "new_books": 0, "archived": 0,
            "covers_found": 0, "covers_missing": 0,
        }

    def is_fiction(self, book: dict) -> bool:
        categories = [c.lower() for c in book.get("categories", [])]
        for cat in categories:
            for exc in FICTION_EXCLUDE_CATEGORIES:
                if exc.lower() in cat:
                    return True

        title = book.get("title", "").lower()
        desc = book.get("description", "").lower()
        text = f"{title} {desc}"

        for pattern in [r'\bnovel\b', r'\bfiction\b', r'\brواية\b',
                        r'\bstories\b', r'\bpoems?\b', r'\broman\b',
                        r'\bشعر\b', r'\bديوان\b', r'\bthriller\b']:
            if re.search(pattern, text, re.IGNORECASE):
                if pattern == r'\bfiction\b' and "non-fiction" in text:
                    continue
                return True

        for kw in FICTION_EXCLUDE_KEYWORDS:
            if kw.lower() in title:
                if kw.lower() == "fiction" and ("non-fiction" in text or "nonfiction" in text):
                    continue
                return True
        return False

    def is_expired(self, book: dict) -> bool:
        parsed = parse_date(book.get("published_date", ""))
        if not parsed:
            return False
        return parsed.date() < CUTOFF_DATE

    def generate_dedup_key(self, book: dict) -> str:
        title = re.sub(r'[^\w\s]', '', book.get("title", "").lower().strip())
        title = re.sub(r'\s+', ' ', title)[:60]
        authors = book.get("authors", [])
        author_key = authors[0].lower().strip()[:30] if authors else ""
        return hashlib.md5(f"{title}|{author_key}".encode('utf-8')).hexdigest()

    def detect_region(self, book: dict) -> Tuple[str, List[str]]:
        text = f"{book.get('title','')} {book.get('description','')} {' '.join(book.get('categories',[]))}".lower()
        detected = {}
        countries = []

        for rid, rc in REGIONS.items():
            score = sum(2 for kw in rc.keywords if kw.lower() in text)
            for c in rc.countries:
                if c.lower() in text:
                    score += 3
                    if c not in countries:
                        countries.append(c)
            if score > 0:
                detected[rid] = score

        if not detected:
            return "global", countries

        best = max(detected.keys(), key=lambda r: detected[r] * (10 if REGIONS[r].priority == 1 else 1))
        return best, countries

    def is_relevant(self, book: dict) -> bool:
        text = f"{book.get('title','')} {book.get('description','')} {' '.join(book.get('categories',[]))}".lower()
        keywords = [
            "corruption", "corrupt", "anti-corruption", "bribery", "embezzlement",
            "kleptocracy", "state capture", "fraud", "money laundering",
            "illicit financial", "transparency", "accountability", "governance",
            "فساد", "رشوة", "اختلاس", "نزاهة", "شفافية", "حوكمة", "غسيل أموال",
            "corruption", "fraude", "gouvernance", "intégrité", "blanchiment",
        ]
        return sum(1 for kw in keywords if kw in text) >= 2

    def detect_book_type(self, book: dict) -> str:
        text = f"{book.get('title','')} {book.get('description','')} {book.get('publisher','')}".lower()
        patterns = {
            "report": ["report", "تقرير", "rapport", "index"],
            "official": ["government", "official", "رسمي", "officiel", "plan national"],
            "legal": ["law", "legal", "criminal", "قانون", "juridique"],
            "policy": ["policy", "strategy", "سياسات", "politique"],
            "case_study": ["case study", "دراسة حالة", "étude de cas"],
            "investigative": ["investigat", "whistleblow", "استقصائي", "enquête"],
            "methodology": ["method", "framework", "approach", "منهج", "méthodologie"],
            "reference": ["handbook", "encyclopedia", "موسوعة", "encyclopédie"],
        }
        for bt, kws in patterns.items():
            for kw in kws:
                if kw in text:
                    return bt
        return "academic"

    def process(self, raw_books: List, existing_books: List[dict] = None) -> List[dict]:
        if existing_books is None:
            existing_books = []

        self.stats["total_raw"] = len(raw_books)
        all_books = list(existing_books)
        existing_ids = {self.generate_dedup_key(b) for b in existing_books}

        for book in raw_books:
            d = book.to_dict() if isinstance(book, BookEntry) else book
            key = self.generate_dedup_key(d)
            if key not in existing_ids:
                all_books.append(d)
                existing_ids.add(key)
                self.stats["new_books"] += 1
            else:
                # 🆕 تحديث الغلاف إذا لم يكن موجودًا
                for existing in all_books:
                    if self.generate_dedup_key(existing) == key:
                        if not existing.get("cover_url") and d.get("cover_url"):
                            existing["cover_url"] = d["cover_url"]
                        if not existing.get("info_url") and d.get("info_url"):
                            existing["info_url"] = d["info_url"]
                        break
                self.stats["removed_duplicate"] += 1

        filtered = []
        seen = set()

        for book in all_books:
            key = self.generate_dedup_key(book)
            if key in seen:
                continue

            if self.is_expired(book):
                self.stats["removed_expired"] += 1
                self._archive_book(book)
                continue
            if self.is_fiction(book):
                self.stats["removed_fiction"] += 1
                continue
            if not self.is_relevant(book):
                self.stats["removed_irrelevant"] += 1
                continue

            pc = book.get("page_count", 0)
            if pc and pc < MIN_PAGES:
                self.stats["removed_short"] += 1
                continue

            if not book.get("region") or book["region"] == "global":
                region, countries = self.detect_region(book)
                book["region"] = region
                if countries:
                    book["countries"] = countries

            if not book.get("book_type") or book["book_type"] == "academic":
                book["book_type"] = self.detect_book_type(book)

            # 🆕 إحصاء الأغلفة
            if book.get("cover_url") and "placeholder" not in book.get("cover_url", ""):
                self.stats["covers_found"] += 1
            else:
                self.stats["covers_missing"] += 1

            seen.add(key)
            filtered.append(book)

        # ترتيب
        def sort_key(b):
            order = {"africa": 0, "arab": 1, "global": 2}
            r = order.get(b.get("region", "global"), 2)
            p = parse_date(b.get("published_date", ""))
            return (r, -(p.timestamp() if p else 0))

        filtered.sort(key=sort_key)
        self.stats["final_count"] = len(filtered)
        return filtered

    def _archive_book(self, book: dict):
        archive_dir = PATHS["archive_dir"]
        os.makedirs(archive_dir, exist_ok=True)
        archive_file = os.path.join(archive_dir, f"expired_{TODAY.strftime('%Y-%m')}.json")

        archive = []
        if os.path.exists(archive_file):
            with open(archive_file, "r", encoding="utf-8") as f:
                archive = json.load(f)

        book["archived_date"] = TODAY.isoformat()
        archive.append(book)

        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(archive, f, ensure_ascii=False, indent=2)
        self.stats["archived"] += 1

    def print_stats(self):
        print(f"\n{'='*50}")
        print("📊 إحصائيات التصفية")
        print(f"{'='*50}")
        for k, v in self.stats.items():
            labels = {
                "total_raw": "📥 إجمالي خام", "new_books": "🆕 جديدة",
                "removed_duplicate": "🔄 مكرر", "removed_expired": "📅 منتهي",
                "removed_fiction": "📖 خيالي", "removed_short": "📏 قصير",
                "removed_irrelevant": "❌ غير ذي صلة", "archived": "📦 مؤرشف",
                "final_count": "✅ النهائي",
                "covers_found": "🖼️ أغلفة موجودة", "covers_missing": "❌ بدون غلاف",
            }
            if k in labels:
                print(f"  {labels[k]:.<25} {v}")
        print(f"{'='*50}")
