"""
📝 مولّد README.md التلقائي
"""

from datetime import datetime
from typing import List, Dict
from config import REGIONS, BOOK_TYPES, TODAY, CUTOFF_DATE, VALIDITY_MONTHS


def generate_readme(books: List[dict], stats: dict) -> str:
    """يولّد محتوى README.md كاملاً"""
    
    # تصنيف الكتب حسب المنطقة
    by_region: Dict[str, List[dict]] = {
        "africa": [], "arab": [], "global": [], "french": []
    }
    reports = []
    
    for book in books:
        region = book.get("region", "global")
        lang = book.get("language", "")
        book_type = book.get("book_type", "")
        
        if book_type == "report":
            reports.append(book)
        elif lang == "FR":
            by_region["french"].append(book)
        elif region in by_region:
            by_region[region].append(book)
        else:
            by_region["global"].append(book)
    
    # العدادات
    total = len(books)
    africa_count = len(by_region["africa"])
    arab_count = len(by_region["arab"])
    global_count = len(by_region["global"])
    french_count = len(by_region["french"])
    report_count = len(reports)
    
    cutoff_str = CUTOFF_DATE.strftime("%B %Y")
    today_str = TODAY.strftime("%Y-%m-%d")
    
    md = f"""<div dir="rtl">

# 📚 مرصد كتب الفساد | Corruption Books Observatory

[![المساهمات مرحب بها](https://img.shields.io/badge/المساهمات-مرحب%20بها-brightgreen.svg)](#-المساهمة)
[![آخر تحديث](https://img.shields.io/badge/آخر%20تحديث-{today_str}-blue.svg)]()
[![كتب](https://img.shields.io/badge/الكتب-{total}-orange.svg)]()
[![تحديث تلقائي](https://img.shields.io/badge/تحديث-يومي%20تلقائي-purple.svg)]()

> 📖 قائمة منسّقة **تتحدّث تلقائيًا يوميًا** للكتب غير الخيالية الصادرة خلال آخر **{VALIDITY_MONTHS} شهرًا**
> حول **الفساد ومكافحته** – بالعربية والإنجليزية والفرنسية.
>
> 🎯 الأولوية: **العالم العربي** و**أفريقيا** – مع تغطية عالمية.
>
> 🤖 آخر تحديث تلقائي: **{today_str}**

---

## ⚙️ معايير الإدراج التلقائي

| المعيار | الشرط |
|---------|-------|
| 📅 تاريخ الصدور | آخر {VALIDITY_MONTHS} شهرًا (منذ {cutoff_str}) |
| 📖 النوع | غير خيالي فقط (أكاديمي، بحثي، تقارير) |
| 🌍 الأولوية | العالم العربي + أفريقيا |
| 🗣️ اللغات | العربية · الإنجليزية · الفرنسية |
| ⏰ التحديث | يومي تلقائي عبر GitHub Actions |
| 🗑️ الانتهاء | يُحذف ويُؤرشف كل كتاب تجاوز {VALIDITY_MONTHS} شهرًا |

---

## 📊 إحصائيات المرصد

| الفئة | العدد |
|------|-------|
| 📚 إجمالي الكتب | **{total}** |
| 🌍 أفريقيا | {africa_count} |
| 🏛️ العالم العربي | {arab_count} |
| 🌐 عالمي/مقارن | {global_count} |
| 🇫🇷 بالفرنسية | {french_count} |
| 📊 تقارير مؤسسية | {report_count} |

---

"""
    
    # ═══ أقسام الكتب ═══
    sections = [
        ("africa", "🌍 كتب عن الفساد في أفريقيا", by_region["africa"]),
        ("arab", "🏛️ كتب عن الفساد في العالم العربي", by_region["arab"]),
        ("global", "🌐 كتب بمنظور عالمي / مقارن", by_region["global"]),
        ("french", "🇫🇷 كتب ومنشورات بالفرنسية", by_region["french"]),
    ]
    
    counter = 1
    for region_id, section_title, section_books in sections:
        if not section_books:
            continue
        
        md += f"## {section_title}\n\n"
        md += "| # | العنوان | المؤلف | الناشر | تاريخ الصدور | اللغة | النوع |\n"
        md += "|---|---------|--------|--------|-------------|-------|------|\n"
        
        for book in section_books:
            authors = ", ".join(book.get("authors", [])[:3])
            if len(book.get("authors", [])) > 3:
                authors += " et al."
            
            type_labels = BOOK_TYPES.get(book.get("book_type", "academic"), {})
            type_label = type_labels.get("ar", "أكاديمي")
            
            md += (
                f"| {counter} "
                f"| **{book.get('title', '')}** "
                f"| {authors} "
                f"| {book.get('publisher', '')} "
                f"| {book.get('published_date', '')} "
                f"| {book.get('language', '')} "
                f"| {type_label} |\n"
            )
            counter += 1
        
        md += "\n---\n\n"
    
    # ═══ التقارير ═══
    if reports:
        md += "## 📊 تقارير ومؤشرات مؤسسية\n\n"
        md += "| # | التقرير | الجهة | التاريخ | الرابط |\n"
        md += "|---|--------|-------|---------|--------|\n"
        
        for i, report in enumerate(reports, 1):
            link = report.get("link", "")
            link_md = f"[↗ الرابط]({link})" if link else "—"
            md += (
                f"| T{i} "
                f"| **{report.get('title', '')}** "
                f"| {report.get('publisher', '')} "
                f"| {report.get('published_date', '')} "
                f"| {link_md} |\n"
            )
        
        md += "\n---\n\n"
    
    # ═══ الموارد الدائمة ═══
    md += """## 🔗 روابط وموارد دائمة

| المورد | الوصف | الرابط |
|--------|-------|--------|
| Transparency International | مؤشر مدركات الفساد | [transparency.org](https://www.transparency.org) |
| UNODC – UNCAC | اتفاقية الأمم المتحدة لمكافحة الفساد | [unodc.org](https://www.unodc.org/corruption/) |
| Mo Ibrahim Foundation | مؤشر إبراهيم للحوكمة الأفريقية | [mo.ibrahim.foundation](https://mo.ibrahim.foundation/iiag) |
| World Bank – WGI | مؤشرات الحوكمة العالمية | [worldbank.org](https://info.worldbank.org/governance/wgi/) |
| UNCAC Coalition | ائتلاف المجتمع المدني العالمي | [uncaccoalition.org](https://uncaccoalition.org/) |

---

"""
    
    # ═══ المساهمة ═══
    md += """## 🤝 المساهمة

### إضافة كتاب يدويًا
أضف الكتاب في ملف `data/manual_entries.json` بالتنسيق التالي:

```json
{
  "title": "عنوان الكتاب",
  "authors": ["المؤلف"],
  "publisher": "الناشر",
  "published_date": "2025-06-15",
  "language": "AR",
  "description": "وصف مختصر",
  "isbn": "978-...",
  "region": "arab",
  "book_type": "academic"
}
