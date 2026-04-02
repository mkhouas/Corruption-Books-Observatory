"""
⚙️ إعدادات مرصد كتب الفساد
Corruption Books Observatory – Configuration
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List

# ──────────────────────────────────────────────
# 📅 نافذة الصلاحية: 24 شهرًا
# ──────────────────────────────────────────────
VALIDITY_MONTHS = 24
TODAY = datetime.utcnow().date()
CUTOFF_DATE = TODAY - timedelta(days=VALIDITY_MONTHS * 30.44)  # ~730 يوم

# ──────────────────────────────────────────────
# 🔍 كلمات البحث حسب اللغة
# ──────────────────────────────────────────────
SEARCH_QUERIES: Dict[str, List[str]] = {
    "en": [
        "corruption Africa",
        "anti-corruption Africa",
        "corruption Arab world",
        "corruption MENA",
        "state capture Africa",
        "kleptocracy Africa",
        "corruption governance Africa",
        "bribery developing countries",
        "corruption Middle East",
        "illicit financial flows Africa",
        "political corruption Africa",
        "corruption Nigeria",
        "corruption South Africa",
        "corruption Kenya",
        "corruption Egypt",
        "corruption Iraq",
        "corruption Tunisia",
        "corruption Morocco",
        "corruption Algeria",
        "anti-corruption policy",
        "corruption transparency accountability",
        "grand corruption",
        "corruption public sector",
    ],
    "ar": [
        "الفساد في العالم العربي",
        "مكافحة الفساد",
        "الفساد السياسي",
        "الفساد الإداري",
        "الحوكمة والفساد",
        "الفساد في أفريقيا",
        "النزاهة والشفافية",
        "غسيل الأموال العربي",
        "الفساد المالي",
        "الرشوة والمحسوبية",
        "أسر الدولة",
        "الفساد والتنمية",
        "هيئات مكافحة الفساد",
    ],
    "fr": [
        "corruption Afrique",
        "anti-corruption Afrique",
        "corruption monde arabe",
        "gouvernance corruption Afrique",
        "lutte contre la corruption",
        "corruption Maghreb",
        "corruption Tunisie Maroc Algérie",
        "kleptocratie Afrique",
        "flux financiers illicites Afrique",
        "corruption secteur public",
        "fraude corruption Afrique francophone",
    ],
}

# ──────────────────────────────────────────────
# 🚫 كلمات الاستبعاد (كتب خيالية / روائية)
# ──────────────────────────────────────────────
FICTION_EXCLUDE_KEYWORDS = [
    # English
    "novel", "fiction", "stories", "short stories", "poetry", "poems",
    "thriller", "mystery novel", "romance", "fantasy", "sci-fi",
    "science fiction", "detective", "suspense novel", "literary fiction",
    # Arabic
    "رواية", "قصص", "قصص قصيرة", "شعر", "ديوان", "مسرحية",
    "أدب", "قصة", "روايات", "خيال", "خيال علمي",
    # French
    "roman", "nouvelle", "nouvelles", "poésie", "fiction",
    "conte", "contes", "théâtre", "récit fictif",
]

FICTION_EXCLUDE_CATEGORIES = [
    "fiction", "literary fiction", "poetry", "drama",
    "juvenile fiction", "young adult fiction",
    "science fiction", "fantasy", "romance",
    "mystery", "thriller", "horror",
]

# ──────────────────────────────────────────────
# 🌍 مناطق ذات أولوية + كلمات الكشف
# ──────────────────────────────────────────────
@dataclass
class RegionConfig:
    id: str
    label_ar: str
    label_en: str
    label_fr: str
    priority: int  # 1 = أعلى أولوية
    keywords: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    color: str = "#0f3460"

REGIONS = {
    "africa": RegionConfig(
        id="africa",
        label_ar="أفريقيا",
        label_en="Africa",
        label_fr="Afrique",
        priority=1,
        color="#27ae60",
        keywords=[
            "africa", "african", "أفريقيا", "أفريقي", "afrique", "africain",
            "sub-saharan", "subsaharan", "sahel",
        ],
        countries=[
            "Nigeria", "South Africa", "Kenya", "Ethiopia", "Ghana",
            "Tanzania", "Uganda", "Rwanda", "Mozambique", "Cameroon",
            "Senegal", "Côte d'Ivoire", "DRC", "Congo", "Zimbabwe",
            "Malawi", "Zambia", "Angola", "Botswana", "Namibia",
            "نيجيريا", "جنوب أفريقيا", "كينيا", "إثيوبيا", "غانا",
            "تنزانيا", "أوغندا", "رواندا", "موزمبيق", "الكاميرون",
            "السنغال", "كوت ديفوار", "الكونغو", "زيمبابوي",
        ],
    ),
    "arab": RegionConfig(
        id="arab",
        label_ar="العالم العربي",
        label_en="Arab World",
        label_fr="Monde arabe",
        priority=1,
        color="#e94560",
        keywords=[
            "arab", "arabic", "MENA", "Middle East", "North Africa",
            "عربي", "العالم العربي", "الشرق الأوسط", "شمال أفريقيا",
            "arabe", "monde arabe", "Moyen-Orient", "Maghreb", "Mashreq",
        ],
        countries=[
            "Egypt", "Iraq", "Syria", "Lebanon", "Jordan", "Palestine",
            "Tunisia", "Morocco", "Algeria", "Libya", "Sudan", "Yemen",
            "Saudi Arabia", "UAE", "Kuwait", "Qatar", "Bahrain", "Oman",
            "مصر", "العراق", "سوريا", "لبنان", "الأردن", "فلسطين",
            "تونس", "المغرب", "الجزائر", "ليبيا", "السودان", "اليمن",
            "السعودية", "الإمارات", "الكويت", "قطر", "البحرين", "عُمان",
            "Égypte", "Irak", "Syrie", "Liban", "Tunisie", "Maroc",
            "Algérie", "Libye", "Soudan", "Yémen",
        ],
    ),
    "global": RegionConfig(
        id="global",
        label_ar="عالمي",
        label_en="Global",
        label_fr="Mondial",
        priority=2,
        color="#0f3460",
        keywords=[
            "global", "international", "comparative", "worldwide",
            "عالمي", "دولي", "مقارن",
            "mondial", "international", "comparé",
        ],
        countries=[],
    ),
}

# ──────────────────────────────────────────────
# 🏷️ تصنيفات الكتب
# ──────────────────────────────────────────────
BOOK_TYPES = {
    "academic": {"ar": "أكاديمي", "en": "Academic", "fr": "Académique"},
    "policy": {"ar": "سياسات", "en": "Policy", "fr": "Politiques"},
    "investigative": {"ar": "استقصائي", "en": "Investigative", "fr": "Enquête"},
    "report": {"ar": "تقرير", "en": "Report", "fr": "Rapport"},
    "legal": {"ar": "قانوني", "en": "Legal", "fr": "Juridique"},
    "reference": {"ar": "مرجعي", "en": "Reference", "fr": "Référence"},
    "case_study": {"ar": "دراسة حالة", "en": "Case Study", "fr": "Étude de cas"},
    "methodology": {"ar": "منهجي", "en": "Methodology", "fr": "Méthodologie"},
    "official": {"ar": "وثيقة رسمية", "en": "Official", "fr": "Officiel"},
}

# ──────────────────────────────────────────────
# 🔌 إعدادات APIs
# ──────────────────────────────────────────────
API_CONFIG = {
    "google_books": {
        "base_url": "https://www.googleapis.com/books/v1/volumes",
        "max_results_per_query": 40,
        "rate_limit_delay": 1.5,  # ثانية بين الطلبات
        "enabled": True,
    },
    "open_library": {
        "search_url": "https://openlibrary.org/search.json",
        "max_results_per_query": 50,
        "rate_limit_delay": 1.0,
        "enabled": True,
    },
    "crossref": {
        "base_url": "https://api.crossref.org/works",
        "max_results_per_query": 50,
        "rate_limit_delay": 1.0,
        "enabled": True,
        "mailto": "observatory@example.com",  # Polite pool
    },
}

# ──────────────────────────────────────────────
# 📂 مسارات الملفات
# ──────────────────────────────────────────────
PATHS = {
    "books_db": "data/books.json",
    "manual_entries": "data/manual_entries.json",
    "archive_dir": "data/archive",
    "readme": "README.md",
    "index_html": "index.html",
}

# ──────────────────────────────────────────────
# 📊 الحد الأدنى لعدد الصفحات
# ──────────────────────────────────────────────
MIN_PAGES = 80
