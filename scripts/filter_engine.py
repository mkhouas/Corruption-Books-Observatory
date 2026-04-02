"""
🔍 محرك التصفية والتنقية
يزيل الكتب الخيالية، والمكررة، والمنتهية الصلاحية
ويُصنّف حسب المنطقة الجغرافية
"""

import json
import os
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import (
    FICTION_EXCLUDE_KEYWORDS, FICTION_EXCLUDE_CATEGORIES,
    REGIONS, CUTOFF_DATE, TODAY, MIN_PAGES, PATHS
)
from fetcher import BookEntry, parse_date


class FilterEngine:
    """محرك تصفية الكتب"""
    
    def __init__(self):
        self.stats = {
            "total_raw": 0,
            "removed_fiction": 0,
            "removed_expired": 0,
            "removed_duplicate": 0,
            "removed_short": 0,
            "removed_irrelevant": 0,
            "final_count": 0,
            "new_books": 0,
            "archived": 0,
        }
    
    # ─────────────────────────────────────
    # 🚫 كشف الكتب الخيالية
    # ─────────────────────────────────────
    def is_fiction(self, book: dict) -> bool:
        """يتحقق هل الكتاب خيالي/روائي"""
        
        # فحص التصنيفات
        categories = [c.lower() for c in book.get("categories", [])]
        for cat in categories:
            for exclude in FICTION_EXCLUDE_CATEGORIES:
                if exclude.lower() in cat:
                    return True
        
        # فحص العنوان والوصف
        title = book.get("title", "").lower()
        description = book.get("description", "").lower()
        text = f"{title} {description}"
        
        fiction_patterns = [
            r'\broman\b', r'\bnovel\b', r'\brواية\b',
            r'\bfiction\b', r'\bstories\b', r'\bقصص\s+قصيرة\b',
            r'\bpoems?\b', r'\bpoetry\b', r'\bشعر\b', r'\bديوان\b',
            r'\bthriller\b', r'\bmystery\b',
        ]
        
        for pattern in fiction_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # كلمات مفتاحية بسيطة
        for keyword in FICTION_EXCLUDE_KEYWORDS:
            kw_lower = keyword.lower()
            if kw_lower in title:
                # استثناء: "fiction" في "non-fiction" أو "science fiction" ككتاب عن الخيال
                if kw_lower == "fiction" and ("non-fiction" in text or "nonfiction" in text):
                    continue
                return True
        
        return False
    
    # ─────────────────────────────────────
    # 📅 فحص الصلاحية (24 شهر)
    # ─────────────────────────────────────
    def is_expired(self, book: dict) -> bool:
        """يتحقق هل تجاوز الكتاب 24 شهرًا"""
        pub_date_str = book.get("published_date", "")
        parsed = parse_date(pub_date_str)
        
        if not parsed:
            # إذا لم نستطع تحليل التاريخ، نحتفظ به مؤقتًا
            return False
        
        return parsed.date() < CUTOFF_DATE
    
    # ─────────────────────────────────────
    # 🔗 كشف المكرر
    # ─────────────────────────────────────
    def generate_dedup_key(self, book: dict) -> str:
        """يولّد مفتاح إزالة التكرار"""
        title = re.sub(r'[^\w\s]', '', book.get("title", "").lower().strip())
        title = re.sub(r'\s+', ' ', title)
        
        # أول 60 حرف من العنوان + أول مؤلف
        title_key = title[:60]
        authors = book.get("authors", [])
        author_key = authors[0].lower().strip()[:30] if authors else ""
        
        raw = f"{title_key}|{author_key}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()
    
    # ─────────────────────────────────────
    # 🌍 تصنيف المنطقة الجغرافية
    # ─────────────────────────────────────
    def detect_region(self, book: dict) -> Tuple[str, List[str]]:
        """يكتشف المنطقة الجغرافية والدول المذكورة"""
        text = (
            f"{book.get('title', '')} "
            f"{book.get('description', '')} "
            f"{' '.join(book.get('categories', []))}"
        ).lower()
        
        detected_regions = {}
        detected_countries = []
        
        for region_id, region_config in REGIONS.items():
            score = 0
            
            # فحص الكلمات المفتاحية
            for kw in region_config.keywords:
                if kw.lower() in text:
                    score += 2
            
            # فحص الدول
            for country in region_config.countries:
                if country.lower() in text:
                    score += 3
                    if country not in detected_countries:
                        detected_countries.append(country)
            
            if score > 0:
                detected_regions[region_id] = score
        
        if not detected_regions:
            return "global", detected_countries
        
        # الأولوية: أفريقيا والعالم العربي أولاً
        best_region = max(
            detected_regions.keys(),
            key=lambda r: (
                detected_regions[r] * (10 if REGIONS[r].priority == 1 else 1)
            )
        )
        
        return best_region, detected_countries
    
    # ─────────────────────────────────────
    # ✅ فحص الصلة بالموضوع
    # ─────────────────────────────────────
    def is_relevant(self, book: dict) -> bool:
        """يتحقق هل الكتاب متعلق فعلاً بالفساد"""
        text = (
            f"{book.get('title', '')} "
            f"{book.get('description', '')} "
            f"{' '.join(book.get('categories', []))}"
        ).lower()
        
        corruption_keywords = [
            "corruption", "corrupt", "anti-corruption", "anticorruption",
            "bribery", "bribe", "embezzlement", "kleptocracy",
            "state capture", "fraud", "money laundering",
            "illicit financial", "transparency", "accountability",
            "governance", "integrity",
            "فساد", "رشوة", "اختلاس", "نزاهة", "شفافية",
            "مكافحة الفساد", "حوكمة", "غسيل أموال", "محسوبية",
            "corruption", "fraude", "gouvernance", "intégrité",
            "blanchiment", "kleptocratie", "pots-de-vin",
        ]
        
        match_count = sum(1 for kw in corruption_keywords if kw in text)
        return match_count >= 2
    
    # ─────────────────────────────────────
    # 🏷️ تحديد نوع الكتاب
    # ─────────────────────────────────────
    def detect_book_type(self, book: dict) -> str:
        """يحدد نوع الكتاب"""
        text = (
            f"{book.get('title', '')} "
            f"{book.get('description', '')} "
            f"{book.get('publisher', '')}"
        ).lower()
        
        type_patterns = {
            "report": ["report", "تقرير", "rapport", "index", "مؤشر"],
            "official": ["government", "official", "رسمي", "حكومي", "officiel", "plan national"],
            "legal": ["law", "legal", "criminal", "قانون", "قانوني", "juridique", "pénal"],
            "policy": ["policy", "strategy", "سياسات", "استراتيجية", "politique"],
            "case_study": ["case study", "case studies", "دراسة حالة", "étude de cas"],
            "investigative": ["investigat", "whistleblow", "استقصائي", "تحقيق", "enquête"],
            "methodology": ["method", "framework", "approach", "منهج", "إطار", "méthodologie"],
            "reference": ["handbook", "encyclopedia", "موسوعة", "مرجع", "encyclopédie"],
        }
        
        for book_type, keywords in type_patterns.items():
            for kw in keywords:
                if kw in text:
                    return book_type
        
        return "academic"
    
    # ─────────────────────────────────────
    # 🔄 التصفية الرئيسية
    # ─────────────────────────────────────
    def process(self, raw_books: List[dict], existing_books: List[dict] = None) -> List[dict]:
        """
        يعالج قائمة الكتب الخام ويعيد القائمة النظيفة
        """
        if existing_books is None:
            existing_books = []
        
        self.stats["total_raw"] = len(raw_books)
        
        # ─── 1. دمج الكتب الجديدة مع القائمة الحالية ───
        all_books = list(existing_books)
        existing_ids = {self.generate_dedup_key(b) for b in existing_books}
        
        for book in raw_books:
            book_dict = book.to_dict() if isinstance(book, BookEntry) else book
            dedup_key = self.generate_dedup_key(book_dict)
            
            if dedup_key not in existing_ids:
                all_books.append(book_dict)
                existing_ids.add(dedup_key)
                self.stats["new_books"] += 1
            else:
                self.stats["removed_duplicate"] += 1
        
        # ─── 2. تصفية شاملة ───
        filtered = []
        seen_keys = set()
        
        for book in all_books:
            # إزالة المكرر
            dedup_key = self.generate_dedup_key(book)
            if dedup_key in seen_keys:
                self.stats["removed_duplicate"] += 1
                continue
            
            # فحص الصلاحية
            if self.is_expired(book):
                self.stats["removed_expired"] += 1
                self._archive_book(book)
                continue
            
            # فحص الخيالي
            if self.is_fiction(book):
                self.stats["removed_fiction"] += 1
                continue
            
            # فحص الصلة
            if not self.is_relevant(book):
                self.stats["removed_irrelevant"] += 1
                continue
            
            # فحص عدد الصفحات (إذا متوفر)
            page_count = book.get("page_count", 0)
            if page_count and page_count < MIN_PAGES:
                self.stats["removed_short"] += 1
                continue
            
            # ─── إثراء البيانات ───
            if not book.get("region") or book.get("region") == "global":
                region, countries = self.detect_region(book)
                book["region"] = region
                if countries:
                    book["countries"] = countries
            
            if not book.get("book_type") or book.get("book_type") == "academic":
                book["book_type"] = self.detect_book_type(book)
            
            seen_keys.add(dedup_key)
            filtered.append(book)
        
        # ─── 3. ترتيب: أفريقيا والعالم العربي أولاً، ثم بالتاريخ ───
        def sort_key(b):
            region_order = {"africa": 0, "arab": 1, "global": 2}
            r = region_order.get(b.get("region", "global"), 2)
            
            parsed = parse_date(b.get("published_date", ""))
            date_val = parsed.timestamp() if parsed else 0
            
            return (r, -date_val)
        
        filtered.sort(key=sort_key)
        
        self.stats["final_count"] = len(filtered)
        
        return filtered
    
    # ─────────────────────────────────────
    # 📦 أرشفة الكتب المنتهية
    # ─────────────────────────────────────
    def _archive_book(self, book: dict):
        """يؤرشف كتابًا منتهي الصلاحية"""
        archive_dir = PATHS["archive_dir"]
        os.makedirs(archive_dir, exist_ok=True)
        
        month_key = TODAY.strftime("%Y-%m")
        archive_file = os.path.join(archive_dir, f"expired_{month_key}.json")
        
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
        """يطبع إحصائيات التصفية"""
        print("\n" + "=" * 50)
        print("📊 إحصائيات التصفية")
        print("=" * 50)
        print(f"  📥 إجمالي خام:        {self.stats['total_raw']}")
        print(f"  🆕 كتب جديدة:        {self.stats['new_books']}")
        print(f"  🔄 مكرر محذوف:       {self.stats['removed_duplicate']}")
        print(f"  📅 منتهي الصلاحية:    {self.stats['removed_expired']}")
        print(f"  📖 خيالي مستبعد:      {self.stats['removed_fiction']}")
        print(f"  📏 قصير جدًا:         {self.stats['removed_short']}")
        print(f"  ❌ غير ذي صلة:       {self.stats['removed_irrelevant']}")
        print(f"  📦 مؤرشف:            {self.stats['archived']}")
        print(f"  ✅ النتيجة النهائية:   {self.stats['final_count']}")
        print("=" * 50)
