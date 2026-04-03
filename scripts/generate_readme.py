"""
📝 مولّد README.md – مع صور أغلفة الكتب
"""

from typing import List, Dict
from config import REGIONS, BOOK_TYPES, TODAY, CUTOFF_DATE, VALIDITY_MONTHS, COVER_CONFIG


def generate_readme(books: List[dict], stats: dict) -> str:

    by_region: Dict[str, List[dict]] = {"africa": [], "arab": [], "global": [], "french": []}
    reports = []

    for book in books:
        bt = book.get("book_type", "")
        lang = book.get("language", "")
        region = book.get("region", "global")
        if bt == "report":
            reports.append(book)
        elif lang == "FR":
            by_region["french"].append(book)
        elif region in by_region:
            by_region[region].append(book)
        else:
            by_region["global"].append(book)

    total = len(books)
    today_str = TODAY.strftime("%Y-%m-%d")
    cutoff_str = CUTOFF_DATE.strftime("%B %Y")
    placeholder = COVER_CONFIG["placeholder_url"]

    md = f"""<div dir="rtl">

# 📚 مرصد كتب الفساد | Corruption Books Observatory

[![تحديث يومي](https://img.shields.io/badge/تحديث-يومي%20تلقائي-purple.svg)]()
[![آخر تحديث](https://img.shields.io/badge/آخر%20تحديث-{today_str}-blue.svg)]()
[![كتب](https://img.shields.io/badge/الكتب-{total}-orange.svg)]()
[![المساهمات](https://img.shields.io/badge/المساهمات-مرحب%20بها-brightgreen.svg)](#-المساهمة)

> 🤖 **يتحدّث تلقائيًا يوميًا** | 📖 كتب غير خيالية فقط | 📅 آخر {VALIDITY_MONTHS} شهرًا
>
> 🎯 الأولوية: **العالم العربي** و**أفريقيا** | 🗣️ عربي · English · Français
>
> 🖼️ **اضغط على أي غلاف للاطلاع على الكتاب مباشرة**

---

## 📊 إحصائيات

| الفئة | العدد |
|------|-------|
| 📚 الإجمالي | **{total}** |
| 🌍 أفريقيا | {len(by_region['africa'])} |
| 🏛️ عربي | {len(by_region['arab'])} |
| 🌐 عالمي | {len(by_region['global'])} |
| 🇫🇷 فرنسي | {len(by_region['french'])} |
| 📊 تقارير | {len(reports)} |
| 🖼️ أغلفة | {stats.get('covers_found', 0)} |

---

"""

    # ═══ بناء أقسام الكتب مع الأغلفة ═══
    sections = [
        ("africa", "🌍 أفريقيا", by_region["africa"]),
        ("arab", "🏛️ العالم العربي", by_region["arab"]),
        ("global", "🌐 عالمي / مقارن", by_region["global"]),
        ("french", "🇫🇷 بالفرنسية", by_region["french"]),
    ]

    counter = 1
    for rid, title, bks in sections:
        if not bks:
            continue

        md += f"## {title}\n\n"

        for book in bks:
            cover = book.get("cover_url", "") or placeholder
            info = book.get("info_url", "") or book.get("link", "") or "#"
            authors = ", ".join(book.get("authors", [])[:3])
            if len(book.get("authors", [])) > 3:
                authors += " et al."

            tl = BOOK_TYPES.get(book.get("book_type", "academic"), {})
            type_label = tl.get("ar", "أكاديمي")
            pub_date = book.get("published_date", "")
            publisher = book.get("publisher", "")
            desc = book.get("description", "")[:200]
            if len(book.get("description", "")) > 200:
                desc += "..."

            md += f"""### {counter}. [{book.get('title', '')}]({info})

<a href="{info}"><img src="{cover}" alt="غلاف" width="120" align="left" style="margin-left:15px; margin-bottom:10px; border-radius:6px;" /></a>

| | |
|---|---|
| ✍️ **المؤلف** | {authors} |
| 🏢 **الناشر** | {publisher} |
| 📅 **التاريخ** | {pub_date} |
| 🗣️ **اللغة** | {book.get('language', '')} |
| 🏷️ **النوع** | {type_label} |

{f'> {desc}' if desc else ''}

[📖 **اطّلع على الكتاب ←**]({info})

<br clear="both"/>

---

"""
            counter += 1

    # ═══ التقارير ═══
    if reports:
        md += "## 📊 تقارير مؤسسية\n\n"
        md += "| # | التقرير | الجهة | التاريخ | الرابط |\n"
        md += "|---|--------|-------|---------|--------|\n"
        for i, r in enumerate(reports, 1):
            link = r.get("info_url", "") or r.get("link", "")
            lnk = f"[↗ اطّلع عليه]({link})" if link else "—"
            md += f"| T{i} | **{r.get('title','')}** | {r.get('publisher','')} | {r.get('published_date','')} | {lnk} |\n"
        md += "\n---\n\n"

    # ═══ الموارد ═══
    md += """## 🔗 موارد دائمة

| المورد | الرابط |
|--------|--------|
| Transparency International | [transparency.org](https://www.transparency.org) |
| UNODC – UNCAC | [unodc.org](https://www.unodc.org/corruption/) |
| Mo Ibrahim Foundation | [mo.ibrahim.foundation](https://mo.ibrahim.foundation/iiag) |
| World Bank – WGI | [worldbank.org](https://info.worldbank.org/governance/wgi/) |
| UNCAC Coalition | [uncaccoalition.org](https://uncaccoalition.org/) |

---

## 🤝 المساهمة

أضف كتبًا في `data/manual_entries.json` – لا تنسَ إضافة حقل `cover_url` و `info_url`:

```json
{
  "title": "عنوان الكتاب",
  "authors": ["المؤلف"],
  "publisher": "الناشر",
  "published_date": "2025-06-15",
  "language": "AR",
  "cover_url": "https://...",
  "info_url": "https://...",
  "region": "arab"
}
