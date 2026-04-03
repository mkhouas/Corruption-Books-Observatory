"""
🔌 جلب الكتب من APIs متعددة – مع أغلفة وروابط
"""

import os
import time
import re
import requests
import hashlib
from datetime import datetime
from typing import List, Optional
from config import API_CONFIG, SEARCH_QUERIES, CUTOFF_DATE, TODAY, MIN_PAGES


class BookEntry:
    """نموذج بيانات كتاب موحّد"""
    def __init__(self, **kwargs):
        self.title: str = kwargs.get("title", "")
        self.authors: List[str] = kwargs.get("authors", [])
        self.publisher: str = kwargs.get("publisher", "")
        self.published_date: str = kwargs.get("published_date", "")
        self.parsed_date: Optional[datetime] = kwargs.get("parsed_date", None)
        self.description: str = kwargs.get("description", "")
        self.isbn: str = kwargs.get("isbn", "")
        self.language: str = kwargs.get("language", "")
        self.page_count: int = kwargs.get("page_count", 0)
        self.categories: List[str] = kwargs.get("categories", [])
        self.source: str = kwargs.get("source", "")
        self.link: str = kwargs.get("link", "")
        self.region: str = kwargs.get("region", "global")
        self.book_type: str = kwargs.get("book_type", "academic")
        self.countries: List[str] = kwargs.get("countries", [])
        self.search_query: str = kwargs.get("search_query", "")
        self.fetch_date: str = TODAY.isoformat()
        # 🆕 حقول الأغلفة والروابط
        self.cover_url: str = kwargs.get("cover_url", "")
        self.info_url: str = kwargs.get("info_url", "")
        self.preview_url: str = kwargs.get("preview_url", "")
        self.buy_url: str = kwargs.get("buy_url", "")

    def generate_id(self) -> str:
        raw = f"{self.title.lower().strip()}|{'|'.join(sorted(a.lower() for a in self.authors))}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "id": self.generate_id(),
            "title": self.title,
            "authors": self.authors,
            "publisher": self.publisher,
            "published_date": self.published_date,
            "description": self.description[:500] if self.description else "",
            "isbn": self.isbn,
            "language": self.language,
            "page_count": self.page_count,
            "categories": self.categories,
            "source": self.source,
            "link": self.link,
            "region": self.region,
            "book_type": self.book_type,
            "countries": self.countries,
            "search_query": self.search_query,
            "fetch_date": self.fetch_date,
            # 🆕
            "cover_url": self.cover_url,
            "info_url": self.info_url,
            "preview_url": self.preview_url,
            "buy_url": self.buy_url,
        }


def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d", "%Y-%m", "%Y", "%d/%m/%Y", "%B %d, %Y",
                "%B %Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    year_match = re.search(r'(20[12]\d)', date_str)
    if year_match:
        try:
            return datetime(int(year_match.group(1)), 1, 1)
        except ValueError:
            pass
    return None


# ═══════════════════════════════════
# 📗 Google Books API
# ═══════════════════════════════════
class GoogleBooksFetcher:
    def __init__(self):
        self.config = API_CONFIG["google_books"]
        self.api_key = os.environ.get("GOOGLE_BOOKS_API_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "CorruptionBooksObservatory/1.0"})

    def fetch(self, query: str, lang_restrict: str = "") -> List[BookEntry]:
        books = []
        params = {
            "q": query,
            "maxResults": 40,
            "startIndex": 0,
            "orderBy": "newest",
            "printType": "books",
        }
        if lang_restrict:
            params["langRestrict"] = lang_restrict
        if self.api_key:
            params["key"] = self.api_key

        try:
            resp = self.session.get(self.config["base_url"], params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠️ Google Books error: {e}")
            return books

        for item in data.get("items", []):
            book = self._parse_item(item, query)
            if book:
                books.append(book)
        return books

    def _parse_item(self, item: dict, query: str) -> Optional[BookEntry]:
        info = item.get("volumeInfo", {})
        title = info.get("title", "")
        if not title:
            return None

        pub_date_str = info.get("publishedDate", "")
        parsed = parse_date(pub_date_str)
        if not parsed or parsed.date() < CUTOFF_DATE:
            return None

        isbn = ""
        for ident in info.get("industryIdentifiers", []):
            if ident.get("type") in ("ISBN_13", "ISBN_10"):
                isbn = ident.get("identifier", "")
                if ident.get("type") == "ISBN_13":
                    break

        lang = info.get("language", "")
        lang_map = {"en": "EN", "ar": "AR", "fr": "FR"}

        # 🆕 استخراج الغلاف والروابط
        image_links = info.get("imageLinks", {})
        cover_url = image_links.get("thumbnail", "") or image_links.get("smallThumbnail", "")
        if cover_url:
            cover_url = cover_url.replace("http://", "https://")
            cover_url = cover_url.replace("&edge=curl", "")
            # رفع الجودة
            cover_url = cover_url.replace("zoom=1", "zoom=2")

        preview_url = info.get("previewLink", "")
        info_url = info.get("infoLink", "")

        # رابط الشراء
        sale_info = item.get("saleInfo", {})
        buy_url = sale_info.get("buyLink", "")

        return BookEntry(
            title=title,
            authors=info.get("authors", []),
            publisher=info.get("publisher", ""),
            published_date=pub_date_str,
            parsed_date=parsed,
            description=info.get("description", ""),
            isbn=isbn,
            language=lang_map.get(lang, lang.upper() if lang else ""),
            page_count=info.get("pageCount", 0),
            categories=info.get("categories", []),
            source="google_books",
            link=info_url,
            search_query=query,
            cover_url=cover_url,
            info_url=info_url,
            preview_url=preview_url,
            buy_url=buy_url,
        )

    def fetch_all(self) -> List[BookEntry]:
        if not self.config["enabled"]:
            return []
        all_books = []
        lang_map = {"en": "en", "ar": "ar", "fr": "fr"}
        for lang, queries in SEARCH_QUERIES.items():
            for query in queries:
                print(f"  📗 Google [{lang.upper()}]: '{query}'")
                books = self.fetch(query, lang_restrict=lang_map.get(lang, ""))
                all_books.extend(books)
                time.sleep(self.config["rate_limit_delay"])
        print(f"  ✅ Google Books: {len(all_books)} نتيجة")
        return all_books


# ═══════════════════════════════════
# 📙 Open Library API
# ═══════════════════════════════════
class OpenLibraryFetcher:
    def __init__(self):
        self.config = API_CONFIG["open_library"]
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "CorruptionBooksObservatory/1.0"})

    def fetch(self, query: str, lang: str = "") -> List[BookEntry]:
        books = []
        params = {
            "q": query, "limit": self.config["max_results_per_query"],
            "sort": "new",
            "fields": "key,title,author_name,publisher,publish_date,isbn,"
                      "language,number_of_pages_median,subject,first_publish_year,cover_i",
        }
        if lang:
            params["language"] = lang

        try:
            resp = self.session.get(self.config["search_url"], params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠️ Open Library error: {e}")
            return books

        for doc in data.get("docs", []):
            book = self._parse_doc(doc, query)
            if book:
                books.append(book)
        return books

    def _parse_doc(self, doc: dict, query: str) -> Optional[BookEntry]:
        title = doc.get("title", "")
        if not title:
            return None

        pub_dates = doc.get("publish_date", [])
        parsed = None
        pub_date_str = ""

        for pd in sorted(pub_dates, reverse=True) if pub_dates else []:
            parsed = parse_date(pd)
            if parsed and parsed.date() >= CUTOFF_DATE:
                pub_date_str = pd
                break

        if not parsed:
            first_year = doc.get("first_publish_year")
            if first_year:
                parsed = parse_date(str(first_year))
                pub_date_str = str(first_year)

        if not parsed or parsed.date() < CUTOFF_DATE:
            return None

        isbns = doc.get("isbn", [])
        isbn = ""
        for i in isbns:
            if len(i) == 13:
                isbn = i
                break
        if not isbn and isbns:
            isbn = isbns[0]

        languages = doc.get("language", [])
        lang_map = {"eng": "EN", "ara": "AR", "fre": "FR", "fra": "FR"}
        language = ""
        for l in languages:
            if l in lang_map:
                language = lang_map[l]
                break

        # 🆕 غلاف Open Library
        cover_id = doc.get("cover_i")
        cover_url = ""
        if cover_id:
            cover_url = f"{self.config['covers_url']}/b/id/{cover_id}-M.jpg"
        elif isbn:
            cover_url = f"{self.config['covers_url']}/b/isbn/{isbn}-M.jpg"

        key = doc.get("key", "")
        info_url = f"https://openlibrary.org{key}" if key else ""

        return BookEntry(
            title=title,
            authors=doc.get("author_name", []),
            publisher=(doc.get("publisher", [""]))[0] if doc.get("publisher") else "",
            published_date=pub_date_str,
            parsed_date=parsed,
            isbn=isbn,
            language=language,
            page_count=doc.get("number_of_pages_median", 0) or 0,
            categories=doc.get("subject", [])[:10],
            source="open_library",
            link=info_url,
            search_query=query,
            cover_url=cover_url,
            info_url=info_url,
        )

    def fetch_all(self) -> List[BookEntry]:
        if not self.config["enabled"]:
            return []
        all_books = []
        ol_lang_map = {"en": "eng", "ar": "ara", "fr": "fre"}
        for lang, queries in SEARCH_QUERIES.items():
            for query in queries:
                print(f"  📙 Open Library [{lang.upper()}]: '{query}'")
                books = self.fetch(query, lang=ol_lang_map.get(lang, ""))
                all_books.extend(books)
                time.sleep(self.config["rate_limit_delay"])
        print(f"  ✅ Open Library: {len(all_books)} نتيجة")
        return all_books


# ═══════════════════════════════════
# 📘 CrossRef API
# ═══════════════════════════════════
class CrossRefFetcher:
    def __init__(self):
        self.config = API_CONFIG["crossref"]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"CorruptionBooksObservatory/1.0 (mailto:{self.config['mailto']})"
        })

    def fetch(self, query: str) -> List[BookEntry]:
        books = []
        params = {
            "query": query,
            "filter": f"type:book,from-pub-date:{CUTOFF_DATE.isoformat()}",
            "rows": self.config["max_results_per_query"],
            "sort": "published", "order": "desc",
        }

        try:
            resp = self.session.get(self.config["base_url"], params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠️ CrossRef error: {e}")
            return books

        for item in data.get("message", {}).get("items", []):
            book = self._parse_item(item, query)
            if book:
                books.append(book)
        return books

    def _parse_item(self, item: dict, query: str) -> Optional[BookEntry]:
        titles = item.get("title", [])
        title = titles[0] if titles else ""
        if not title:
            return None

        date_parts = (
            item.get("published-print", {}).get("date-parts", [[]])[0]
            or item.get("published-online", {}).get("date-parts", [[]])[0]
        )
        if not date_parts or not date_parts[0]:
            return None

        year = date_parts[0]
        month = date_parts[1] if len(date_parts) > 1 else 1
        day = date_parts[2] if len(date_parts) > 2 else 1

        try:
            parsed = datetime(year, month, day)
        except (ValueError, TypeError):
            return None

        if parsed.date() < CUTOFF_DATE:
            return None

        authors = []
        for a in item.get("author", []):
            given = a.get("given", "")
            family = a.get("family", "")
            authors.append(f"{given} {family}".strip() if given else family)

        isbns = item.get("ISBN", [])
        isbn = isbns[0] if isbns else ""
        doi = item.get("DOI", "")

        return BookEntry(
            title=title,
            authors=authors,
            publisher=item.get("publisher", ""),
            published_date=parsed.strftime("%Y-%m-%d"),
            parsed_date=parsed,
            isbn=isbn,
            language=item.get("language", "").upper(),
            categories=item.get("subject", []),
            source="crossref",
            link=f"https://doi.org/{doi}" if doi else "",
            search_query=query,
            info_url=f"https://doi.org/{doi}" if doi else "",
        )

    def fetch_all(self) -> List[BookEntry]:
        if not self.config["enabled"]:
            return []
        all_books = []
        for lang in ["en", "fr"]:
            for query in SEARCH_QUERIES.get(lang, []):
                print(f"  📘 CrossRef [{lang.upper()}]: '{query}'")
                books = self.fetch(query)
                all_books.extend(books)
                time.sleep(self.config["rate_limit_delay"])
        print(f"  ✅ CrossRef: {len(all_books)} نتيجة")
        return all_books


# ═══════════════════════════════════
# 🔄 المُجمِّع الرئيسي
# ═══════════════════════════════════
class BooksFetcher:
    def __init__(self):
        self.fetchers = [
            GoogleBooksFetcher(),
            OpenLibraryFetcher(),
            CrossRefFetcher(),
        ]

    def fetch_all_sources(self) -> List[BookEntry]:
        all_books = []
        for fetcher in self.fetchers:
            name = fetcher.__class__.__name__
            print(f"\n{'='*50}\n🔌 {name}\n{'='*50}")
            try:
                books = fetcher.fetch_all()
                all_books.extend(books)
            except Exception as e:
                print(f"  ❌ خطأ: {e}")
        print(f"\n📊 إجمالي خام: {len(all_books)}")
        return all_books
