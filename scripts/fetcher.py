"""
🔌 جلب الكتب من APIs متعددة
Fetches books from Google Books, Open Library, and CrossRef
"""

import os
import time
import requests
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from config import (
    API_CONFIG, SEARCH_QUERIES, CUTOFF_DATE, TODAY,
    MIN_PAGES
)


class BookEntry:
    """نموذج بيانات كتاب موحّد"""
    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", "")
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
    
    def generate_id(self) -> str:
        """يولّد معرّفًا فريدًا بناءً على العنوان والمؤلفين"""
        raw = f"{self.title.lower().strip()}|{'|'.join(sorted(a.lower() for a in self.authors))}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id or self.generate_id(),
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
        }


def parse_date(date_str: str) -> Optional[datetime]:
    """يحلّل تنسيقات تاريخ متنوعة"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%B %Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # محاولة استخراج السنة فقط
    import re
    year_match = re.search(r'(20[12]\d)', date_str)
    if year_match:
        try:
            return datetime(int(year_match.group(1)), 1, 1)
        except ValueError:
            pass
    
    return None


# ═══════════════════════════════════════════════════
# 📗 Google Books API
# ═══════════════════════════════════════════════════
class GoogleBooksFetcher:
    """جلب الكتب من Google Books API"""
    
    def __init__(self):
        self.config = API_CONFIG["google_books"]
        self.api_key = os.environ.get("GOOGLE_BOOKS_API_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CorruptionBooksObservatory/1.0"
        })
    
    def fetch(self, query: str, lang_restrict: str = "") -> List[BookEntry]:
        """جلب الكتب لاستعلام واحد"""
        books = []
        start_index = 0
        max_results = self.config["max_results_per_query"]
        
        while start_index < max_results:
            params = {
                "q": query,
                "maxResults": min(40, max_results - start_index),
                "startIndex": start_index,
                "orderBy": "newest",
                "printType": "books",
            }
            
            if lang_restrict:
                params["langRestrict"] = lang_restrict
            
            if self.api_key:
                params["key"] = self.api_key
            
            try:
                resp = self.session.get(
                    self.config["base_url"],
                    params=params,
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"  ⚠️ Google Books error for '{query}': {e}")
                break
            
            items = data.get("items", [])
            if not items:
                break
            
            for item in items:
                book = self._parse_item(item, query)
                if book:
                    books.append(book)
            
            start_index += len(items)
            
            if len(items) < 40:
                break
            
            time.sleep(self.config["rate_limit_delay"])
        
        return books
    
    def _parse_item(self, item: dict, query: str) -> Optional[BookEntry]:
        """تحويل عنصر Google Books إلى BookEntry"""
        info = item.get("volumeInfo", {})
        
        title = info.get("title", "")
        if not title:
            return None
        
        # تاريخ النشر
        pub_date_str = info.get("publishedDate", "")
        parsed = parse_date(pub_date_str)
        
        # تصفية التاريخ: فقط آخر 24 شهر
        if not parsed or parsed.date() < CUTOFF_DATE:
            return None
        
        # ISBNs
        isbn = ""
        for identifier in info.get("industryIdentifiers", []):
            if identifier.get("type") in ("ISBN_13", "ISBN_10"):
                isbn = identifier.get("identifier", "")
                if identifier.get("type") == "ISBN_13":
                    break
        
        # اللغة
        lang = info.get("language", "")
        lang_map = {"en": "EN", "ar": "AR", "fr": "FR"}
        language = lang_map.get(lang, lang.upper() if lang else "")
        
        return BookEntry(
            title=title,
            authors=info.get("authors", []),
            publisher=info.get("publisher", ""),
            published_date=pub_date_str,
            parsed_date=parsed,
            description=info.get("description", ""),
            isbn=isbn,
            language=language,
            page_count=info.get("pageCount", 0),
            categories=info.get("categories", []),
            source="google_books",
            link=info.get("infoLink", ""),
            search_query=query,
        )
    
    def fetch_all(self) -> List[BookEntry]:
        """جلب من جميع الاستعلامات"""
        if not self.config["enabled"]:
            print("  ⏭️ Google Books: معطّل")
            return []
        
        all_books = []
        
        lang_map = {"en": "en", "ar": "ar", "fr": "fr"}
        
        for lang, queries in SEARCH_QUERIES.items():
            lang_code = lang_map.get(lang, "")
            for query in queries:
                print(f"  📗 Google Books [{lang.upper()}]: '{query}'")
                books = self.fetch(query, lang_restrict=lang_code)
                all_books.extend(books)
                time.sleep(self.config["rate_limit_delay"])
        
        print(f"  ✅ Google Books: {len(all_books)} نتيجة خام")
        return all_books


# ═══════════════════════════════════════════════════
# 📙 Open Library API
# ═══════════════════════════════════════════════════
class OpenLibraryFetcher:
    """جلب الكتب من Open Library API"""
    
    def __init__(self):
        self.config = API_CONFIG["open_library"]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CorruptionBooksObservatory/1.0"
        })
    
    def fetch(self, query: str, lang: str = "") -> List[BookEntry]:
        """جلب الكتب لاستعلام واحد"""
        books = []
        
        params = {
            "q": query,
            "limit": self.config["max_results_per_query"],
            "sort": "new",
            "fields": "key,title,author_name,publisher,publish_date,isbn,"
                      "language,number_of_pages_median,subject,first_publish_year",
        }
        
        if lang:
            params["language"] = lang
        
        try:
            resp = self.session.get(
                self.config["search_url"],
                params=params,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠️ Open Library error for '{query}': {e}")
            return books
        
        for doc in data.get("docs", []):
            book = self._parse_doc(doc, query)
            if book:
                books.append(book)
        
        return books
    
    def _parse_doc(self, doc: dict, query: str) -> Optional[BookEntry]:
        """تحويل مستند Open Library إلى BookEntry"""
        title = doc.get("title", "")
        if not title:
            return None
        
        # تاريخ النشر
        pub_dates = doc.get("publish_date", [])
        first_year = doc.get("first_publish_year")
        
        pub_date_str = ""
        parsed = None
        
        if pub_dates:
            # أحدث تاريخ
            for pd in sorted(pub_dates, reverse=True):
                parsed = parse_date(pd)
                if parsed and parsed.date() >= CUTOFF_DATE:
                    pub_date_str = pd
                    break
        
        if not parsed and first_year:
            parsed = parse_date(str(first_year))
            pub_date_str = str(first_year)
        
        if not parsed or parsed.date() < CUTOFF_DATE:
            return None
        
        # ISBN
        isbns = doc.get("isbn", [])
        isbn = ""
        for i in isbns:
            if len(i) == 13:
                isbn = i
                break
        if not isbn and isbns:
            isbn = isbns[0]
        
        # اللغة
        languages = doc.get("language", [])
        lang_map = {"eng": "EN", "ara": "AR", "fre": "FR", "fra": "FR"}
        language = ""
        for l in languages:
            if l in lang_map:
                language = lang_map[l]
                break
        
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
            link=f"https://openlibrary.org{doc['key']}" if doc.get("key") else "",
            search_query=query,
        )
    
    def fetch_all(self) -> List[BookEntry]:
        """جلب من جميع الاستعلامات"""
        if not self.config["enabled"]:
            print("  ⏭️ Open Library: معطّل")
            return []
        
        all_books = []
        ol_lang_map = {"en": "eng", "ar": "ara", "fr": "fre"}
        
        for lang, queries in SEARCH_QUERIES.items():
            ol_lang = ol_lang_map.get(lang, "")
            for query in queries:
                print(f"  📙 Open Library [{lang.upper()}]: '{query}'")
                books = self.fetch(query, lang=ol_lang)
                all_books.extend(books)
                time.sleep(self.config["rate_limit_delay"])
        
        print(f"  ✅ Open Library: {len(all_books)} نتيجة خام")
        return all_books


# ═══════════════════════════════════════════════════
# 📘 CrossRef API
# ═══════════════════════════════════════════════════
class CrossRefFetcher:
    """جلب الكتب الأكاديمية من CrossRef API"""
    
    def __init__(self):
        self.config = API_CONFIG["crossref"]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"CorruptionBooksObservatory/1.0 "
                          f"(mailto:{self.config['mailto']})"
        })
    
    def fetch(self, query: str) -> List[BookEntry]:
        """جلب الكتب لاستعلام واحد"""
        books = []
        
        # فقط الكتب (وليس المقالات)
        params = {
            "query": query,
            "filter": f"type:book,from-pub-date:{CUTOFF_DATE.isoformat()}",
            "rows": self.config["max_results_per_query"],
            "sort": "published",
            "order": "desc",
            "select": "title,author,publisher,published-print,"
                      "published-online,ISBN,language,type,DOI,link,subject",
        }
        
        try:
            resp = self.session.get(
                self.config["base_url"],
                params=params,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠️ CrossRef error for '{query}': {e}")
            return books
        
        for item in data.get("message", {}).get("items", []):
            book = self._parse_item(item, query)
            if book:
                books.append(book)
        
        return books
    
    def _parse_item(self, item: dict, query: str) -> Optional[BookEntry]:
        """تحويل عنصر CrossRef إلى BookEntry"""
        titles = item.get("title", [])
        title = titles[0] if titles else ""
        if not title:
            return None
        
        # تاريخ النشر
        pub_date_parts = (
            item.get("published-print", {}).get("date-parts", [[]])[0]
            or item.get("published-online", {}).get("date-parts", [[]])[0]
        )
        
        if not pub_date_parts:
            return None
        
        year = pub_date_parts[0] if len(pub_date_parts) > 0 else None
        month = pub_date_parts[1] if len(pub_date_parts) > 1 else 1
        day = pub_date_parts[2] if len(pub_date_parts) > 2 else 1
        
        if not year:
            return None
        
        try:
            parsed = datetime(year, month, day)
        except (ValueError, TypeError):
            return None
        
        if parsed.date() < CUTOFF_DATE:
            return None
        
        pub_date_str = parsed.strftime("%Y-%m-%d")
        
        # المؤلفون
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if family:
                name = f"{given} {family}".strip() if given else family
                authors.append(name)
        
        # ISBN
        isbns = item.get("ISBN", [])
        isbn = isbns[0] if isbns else ""
        
        # اللغة
        language = item.get("language", "").upper()
        if language == "EN":
            language = "EN"
        
        # DOI link
        doi = item.get("DOI", "")
        link = f"https://doi.org/{doi}" if doi else ""
        
        return BookEntry(
            title=title,
            authors=authors,
            publisher=item.get("publisher", ""),
            published_date=pub_date_str,
            parsed_date=parsed,
            isbn=isbn,
            language=language,
            categories=item.get("subject", []),
            source="crossref",
            link=link,
            search_query=query,
        )
    
    def fetch_all(self) -> List[BookEntry]:
        """جلب من جميع الاستعلامات"""
        if not self.config["enabled"]:
            print("  ⏭️ CrossRef: معطّل")
            return []
        
        all_books = []
        
        # CrossRef يستخدم الإنجليزية بشكل أساسي
        for lang in ["en", "fr"]:
            for query in SEARCH_QUERIES.get(lang, []):
                print(f"  📘 CrossRef [{lang.upper()}]: '{query}'")
                books = self.fetch(query)
                all_books.extend(books)
                time.sleep(self.config["rate_limit_delay"])
        
        print(f"  ✅ CrossRef: {len(all_books)} نتيجة خام")
        return all_books


# ═══════════════════════════════════════════════════
# 🔄 المُجمِّع الرئيسي
# ═══════════════════════════════════════════════════
class BooksFetcher:
    """يجمّع كل المصادر في جلب واحد"""
    
    def __init__(self):
        self.fetchers = [
            GoogleBooksFetcher(),
            OpenLibraryFetcher(),
            CrossRefFetcher(),
        ]
    
    def fetch_all_sources(self) -> List[BookEntry]:
        """جلب من جميع المصادر"""
        all_books = []
        
        for fetcher in self.fetchers:
            name = fetcher.__class__.__name__
            print(f"\n{'='*50}")
            print(f"🔌 جارٍ الجلب من: {name}")
            print(f"{'='*50}")
            
            try:
                books = fetcher.fetch_all()
                all_books.extend(books)
            except Exception as e:
                print(f"  ❌ خطأ في {name}: {e}")
                continue
        
        print(f"\n📊 إجمالي النتائج الخام: {len(all_books)}")
        return all_books
