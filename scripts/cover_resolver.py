"""
🖼️ محرك البحث عن أغلفة الكتب
يبحث عبر مصادر متعددة ويختار أفضل غلاف متوفر
"""

import requests
import time
from typing import Optional, Tuple
from config import API_CONFIG, COVER_CONFIG


class CoverResolver:
    """يبحث عن غلاف الكتاب ورابطه من مصادر متعددة"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CorruptionBooksObservatory/1.0"
        })
        self.cache = {}
        self.stats = {"resolved": 0, "failed": 0, "cached": 0}

    def resolve(self, book: dict) -> Tuple[str, str]:
        """
        يبحث عن غلاف ورابط الكتاب
        يُعيد: (cover_url, info_url)
        """
        title = book.get("title", "")
        isbn = book.get("isbn", "")
        source = book.get("source", "")

        # التحقق من الكاش
        cache_key = f"{isbn or title[:50]}"
        if cache_key in self.cache:
            self.stats["cached"] += 1
            return self.cache[cache_key]

        cover_url = ""
        info_url = book.get("link", "")

        # ─── المحاولة 1: من بيانات الكتاب مباشرة ───
        if book.get("cover_url"):
            cover_url = book["cover_url"]

        # ─── المحاولة 2: Google Books API ───
        if not cover_url:
            cover_url, gb_link = self._try_google_books(isbn, title)
            if gb_link and not info_url:
                info_url = gb_link

        # ─── المحاولة 3: Open Library Covers ───
        if not cover_url and isbn:
            cover_url, ol_link = self._try_open_library_isbn(isbn)
            if ol_link and not info_url:
                info_url = ol_link

        # ─── المحاولة 4: Open Library بالبحث ───
        if not cover_url:
            cover_url, ol_link = self._try_open_library_search(title, book.get("authors", []))
            if ol_link and not info_url:
                info_url = ol_link

        # ─── الصورة البديلة ───
        if not cover_url:
            cover_url = COVER_CONFIG["placeholder_url"]
            self.stats["failed"] += 1
        else:
            # تأمين الرابط (HTTPS)
            cover_url = cover_url.replace("http://", "https://")
            self.stats["resolved"] += 1

        # حفظ في الكاش
        self.cache[cache_key] = (cover_url, info_url)
        return cover_url, info_url

    # ═══════════════════════════════════════
    # 📗 Google Books
    # ═══════════════════════════════════════
    def _try_google_books(self, isbn: str, title: str) -> Tuple[str, str]:
        """محاولة جلب الغلاف من Google Books"""
        query = f"isbn:{isbn}" if isbn else title
        if not query:
            return "", ""

        params = {
            "q": query,
            "maxResults": 1,
            "fields": "items(volumeInfo(imageLinks,infoLink,previewLink))",
        }

        try:
            resp = self.session.get(
                API_CONFIG["google_books"]["base_url"],
                params=params,
                timeout=COVER_CONFIG["timeout"]
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            if not items:
                return "", ""

            info = items[0].get("volumeInfo", {})
            image_links = info.get("imageLinks", {})

            # أفضل جودة متاحة
            cover = (
                image_links.get("thumbnail", "")
                or image_links.get("smallThumbnail", "")
            )

            # تحسين جودة الصورة
            if cover:
                cover = cover.replace("zoom=1", f"zoom={COVER_CONFIG['google_books_zoom']}")
                cover = cover.replace("&edge=curl", "")

            link = info.get("previewLink", "") or info.get("infoLink", "")
            return cover, link

        except Exception:
            return "", ""

    # ═══════════════════════════════════════
    # 📙 Open Library – ISBN
    # ═══════════════════════════════════════
    def _try_open_library_isbn(self, isbn: str) -> Tuple[str, str]:
        """محاولة جلب الغلاف من Open Library عبر ISBN"""
        if not isbn:
            return "", ""

        size = COVER_CONFIG["open_library_size"]
        cover_url = f"{API_CONFIG['open_library']['covers_url']}/b/isbn/{isbn}-{size}.jpg"

        # التحقق أن الصورة موجودة فعلاً
        try:
            resp = self.session.head(cover_url, timeout=COVER_CONFIG["timeout"], allow_redirects=True)
            if resp.status_code == 200:
                content_length = resp.headers.get("content-length", "0")
                # صورة placeholder من OL عادةً أقل من 1KB
                if int(content_length) > 1000:
                    info_url = f"https://openlibrary.org/isbn/{isbn}"
                    return cover_url, info_url
        except Exception:
            pass

        return "", ""

    # ═══════════════════════════════════════
    # 📙 Open Library – بحث
    # ═══════════════════════════════════════
    def _try_open_library_search(self, title: str, authors: list) -> Tuple[str, str]:
        """محاولة جلب الغلاف من Open Library عبر البحث"""
        if not title:
            return "", ""

        query = title
        if authors:
            query += f" {authors[0]}"

        params = {
            "q": query,
            "limit": 3,
            "fields": "key,cover_i,isbn,edition_key",
        }

        try:
            resp = self.session.get(
                API_CONFIG["open_library"]["search_url"],
                params=params,
                timeout=COVER_CONFIG["timeout"]
            )
            resp.raise_for_status()
            data = resp.json()

            for doc in data.get("docs", []):
                cover_id = doc.get("cover_i")
                if cover_id:
                    size = COVER_CONFIG["open_library_size"]
                    cover_url = f"{API_CONFIG['open_library']['covers_url']}/b/id/{cover_id}-{size}.jpg"
                    
                    key = doc.get("key", "")
                    info_url = f"https://openlibrary.org{key}" if key else ""
                    
                    return cover_url, info_url

                # محاولة عبر ISBN
                isbns = doc.get("isbn", [])
                for isbn in isbns[:2]:
                    cover_url, info_url = self._try_open_library_isbn(isbn)
                    if cover_url:
                        return cover_url, info_url

        except Exception:
            pass

        return "", ""

    def print_stats(self):
        """طباعة إحصائيات الأغلفة"""
        total = self.stats["resolved"] + self.stats["failed"]
        print(f"\n{'='*50}")
        print(f"🖼️ إحصائيات الأغلفة")
        print(f"{'='*50}")
        print(f"  ✅ أغلفة محل��لة:  {self.stats['resolved']}")
        print(f"  ❌ بدون غلاف:     {self.stats['failed']}")
        print(f"  💾 من الكاش:       {self.stats['cached']}")
        if total > 0:
            pct = (self.stats['resolved'] / total) * 100
            print(f"  📊 نسبة النجاح:   {pct:.1f}%")
        print(f"{'='*50}")
