"""
⚙️ إعدادات مرصد كتب الفساد
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List

# ──────────────────────────────────────
# 📅 نافذة الصلاحية
# ──────────────────────────────────────
VALIDITY_MONTHS = 24
TODAY = datetime.utcnow().date()
CUTOFF_DATE = TODAY - timedelta(days=VALIDITY_MONTHS * 30.44)

# ──────────────────────────────────────
# 🔍 كلمات البحث
# ──────────────────────────────────────
SEARCH_QUERIES: Dict[str, List[str]] = {
    "en": [
        "corruption Africa",
        "anti-corruption Africa",
        "corruption Arab world",
        "corruption MENA",
        "state capture Africa",
        "kleptocracy Africa",
        "corruption governance Africa",
        "corruption Middle East",
        "illicit financial flows Africa",
        "political corruption Africa",
        "corruption Nigeria",
        "corruption South Africa",
        "corruption Kenya",
        "corruption Egypt",
        "corruption Iraq",
        "corruption Tunisia Morocco Algeria",
        "anti-corruption policy",
        "grand corruption",
        "corruption public sector",
        "corruption transparency accountability",
        "bribery developing countries",
    ],
    "ar": [
        "الفساد في العالم العربي",
        "مكافحة الفساد",
        "الفساد السياسي",
        "الفساد الإداري",
        "الحوكمة والفساد",
        "الفساد في أفريقيا",
        "النزاهة والشفافية",
        "غسيل الأموال",
        "الفساد المالي",
        "الرشوة والمحسوبية",
        "الفساد والتنمية",
    ],
    "fr": [
        "corruption Afrique",
        "anti-corruption Afrique",
        "corruption monde arabe",
        "gouvernance corruption Afrique",
        "lutte contre la corruption",
        "corruption Maghreb",
        "corruption Tunisie Maroc Algérie",
        "flux financiers illicites Afrique",
        "corruption secteur public",
        "fraude corruption Afrique francophone",
    ],
}

# ──────────────────────────────────────
# 🚫 استبعاد الخيال
# ──────────────────────────────────────
FICTION_EXCLUDE_KEYWORDS = [
    "novel", "fiction", "stories", "short stories", "poetry", "poems",
    "thriller", "mystery novel", "romance", "fantasy", "sci-fi",
    "science fiction", "detective", "suspense novel",
    "رواية", "قصص", "قصص قصيرة", "شعر", "ديوان", "مسرحية",
    "roman", "nouvelle", "nouvelles", "poésie", "conte", "théâtre",
]

FICTION_EXCLUDE_CATEGORIES = [
    "fiction", "literary fiction", "poetry", "drama",
    "juvenile fiction", "young adult fiction",
    "science fiction", "fantasy", "romance",
    "mystery", "thriller", "horror",
]

# ──────────────────────────────────────
# 🌍 مناطق
# ──────────────────────────────────────
@dataclass
class RegionConfig:
    id: str
    label_ar: str
    label_en: str
    priority: int
    keywords: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    color: str = "#0f3460"
    icon: str = "🌐"

REGIONS = {
    "africa": RegionConfig(
        id="africa", label_ar="أفريقيا", label_en="Africa",
        priority=1, color="#27ae60", icon="🌍",
        keywords=["africa", "african", "أفريقيا", "afrique", "africain", "sub-saharan", "sahel"],
        countries=[
            "Nigeria", "South Africa", "Kenya", "Ethiopia", "Ghana",
            "Tanzania", "Uganda", "Rwanda", "Mozambique", "Cameroon",
            "Senegal", "Côte d'Ivoire", "DRC", "Congo", "Zimbabwe",
            "نيجيريا", "جنوب أفريقيا", "كينيا", "غانا", "رواندا",
        ],
    ),
    "arab": RegionConfig(
        id="arab", label_ar="العالم العربي", label_en="Arab World",
        priority=1, color="#e94560", icon="🏛️",
        keywords=["arab", "MENA", "Middle East", "عربي", "الشرق الأوسط", "arabe", "Maghreb"],
        countries=[
            "Egypt", "Iraq", "Syria", "Lebanon", "Jordan", "Palestine",
            "Tunisia", "Morocco", "Algeria", "Libya", "Sudan", "Yemen",
            "Saudi Arabia", "UAE", "Kuwait", "Qatar",
            "مصر", "العراق", "سوريا", "لبنان", "تونس", "المغرب", "الجزائر",
        ],
    ),
    "global": RegionConfig(
        id="global", label_ar="عالمي", label_en="Global",
        priority=2, color="#0f3460", icon="🌐",
        keywords=["global", "international", "comparative", "عالمي", "دولي"],
        countries=[],
    ),
}

# ──────────────────────────────────────
# 🏷️ أنواع الكتب
# ──────────────────────────────────────
BOOK_TYPES = {
    "academic":      {"ar": "أكاديمي",      "en": "Academic"},
    "policy":        {"ar": "سياسات",       "en": "Policy"},
    "investigative": {"ar": "استقصائي",     "en": "Investigative"},
    "report":        {"ar": "تقرير",        "en": "Report"},
    "legal":         {"ar": "قانوني",       "en": "Legal"},
    "reference":     {"ar": "مرجعي",        "en": "Reference"},
    "case_study":    {"ar": "دراسة حالة",   "en": "Case Study"},
    "methodology":   {"ar": "منهجي",        "en": "Methodology"},
    "official":      {"ar": "وثيقة رسمية",  "en": "Official"},
}

# ──────────────────────────────────────
# 🖼️ إعدادات الأغلفة
# ──────────────────────────────────────
COVER_CONFIG = {
    "google_books_zoom": 1,           # 0=صغير, 1=متوسط, 2=كبير
    "open_library_size": "M",         # S, M, L
    "fallback_placeholder": "assets/no-cover.svg",
    "placeholder_url": "https://via.placeholder.com/128x192/1a1a2e/ffffff?text=📚",
    "max_retries": 2,
    "timeout": 8,
}

# ──────────────────────────────────────
# 🔌 إعدادات APIs
# ──────────────────────────────────────
API_CONFIG = {
    "google_books": {
        "base_url": "https://www.googleapis.com/books/v1/volumes",
        "max_results_per_query": 40,
        "rate_limit_delay": 1.5,
        "enabled": True,
    },
    "open_library": {
        "search_url": "https://openlibrary.org/search.json",
        "covers_url": "https://covers.openlibrary.org",
        "max_results_per_query": 50,
        "rate_limit_delay": 1.0,
        "enabled": True,
    },
    "crossref": {
        "base_url": "https://api.crossref.org/works",
        "max_results_per_query": 50,
        "rate_limit_delay": 1.0,
        "enabled": True,
        "mailto": "observatory@example.com",
    },
}

# ──────────────────────────────────────
# 📂 مسارات الملفات
# ──────────────────────────────────────
PATHS = {
    "books_db": "data/books.json",
    "manual_entries": "data/manual_entries.json",
    "archive_dir": "data/archive",
    "readme": "README.md",
    "index_html": "index.html",
}

MIN_PAGES = 80
