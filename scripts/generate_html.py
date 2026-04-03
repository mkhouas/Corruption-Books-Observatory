"""
🌐 مولّد index.html – مع أغلفة الكتب كروابط مباشرة
"""

from typing import List, Dict
from config import REGIONS, BOOK_TYPES, TODAY, CUTOFF_DATE, VALIDITY_MONTHS, COVER_CONFIG


def generate_html(books: List[dict], stats: dict) -> str:

    by_region: Dict[str, List[dict]] = {"africa": [], "arab": [], "global": [], "french": []}
    reports = []

    for book in books:
        region = book.get("region", "global")
        lang = book.get("language", "")
        bt = book.get("book_type", "")

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
    placeholder = COVER_CONFIG["placeholder_url"]

    # ═══ بناء بطاقة كتاب ═══
    def card(book: dict, num: int, category: str) -> str:
        authors = ", ".join(book.get("authors", [])[:3])
        if len(book.get("authors", [])) > 3:
            authors += " et al."

        tl = BOOK_TYPES.get(book.get("book_type", "academic"), {})
        type_label = tl.get("ar", "أكاديمي")

        desc = book.get("description", "")[:250]
        if len(book.get("description", "")) > 250:
            desc += "..."

        cover = book.get("cover_url", "") or placeholder
        info = book.get("info_url", "") or book.get("link", "") or book.get("preview_url", "")
        buy = book.get("buy_url", "")
        pub_date = book.get("published_date", "")
        lang = book.get("language", "")
        publisher = book.get("publisher", "")
        region_label = REGIONS.get(book.get("region", "global"), REGIONS["global"]).label_ar
        countries = book.get("countries", [])

        # روابط الإجراءات
        actions = ""
        if info:
            actions += f'<a href="{info}" target="_blank" rel="noopener" class="action-btn info-btn" title="معلومات الكتاب">📖 اطّلع عليه</a>'
        if buy:
            actions += f'<a href="{buy}" target="_blank" rel="noopener" class="action-btn buy-btn" title="شراء الكتاب">🛒 اشترِ</a>'
        if book.get("preview_url"):
            actions += f'<a href="{book["preview_url"]}" target="_blank" rel="noopener" class="action-btn preview-btn" title="معاينة">👁️ معاينة</a>'

        countries_html = f'<span class="meta-item">📍 {", ".join(countries[:3])}</span>' if countries else ""

        return f"""
        <div class="book-card {category}" data-category="{category}" data-searchable="{book.get('title','').lower()} {' '.join(book.get('authors',[])).lower()} {publisher.lower()}">
            <span class="book-number">{num}</span>
            <div class="book-inner">
                <a href="{info or '#'}" target="_blank" rel="noopener" class="cover-link" title="اطّلع على الكتاب">
                    <div class="cover-wrapper">
                        <img src="{cover}" 
                             alt="غلاف: {book.get('title','')}" 
                             class="book-cover"
                             loading="lazy"
                             onerror="this.onerror=null; this.src='{placeholder}'; this.classList.add('cover-fallback');">
                        <div class="cover-overlay">
                            <span>📖 اطّلع عليه</span>
                        </div>
                    </div>
                </a>
                <div class="book-details">
                    <div class="book-title">
                        <a href="{info or '#'}" target="_blank" rel="noopener">{book.get('title','')}</a>
                    </div>
                    <div class="book-meta">
                        <span class="meta-item">✍️ {authors}</span>
                        <span class="meta-item">🏢 {publisher}</span>
                        <span class="meta-item">📅 {pub_date}</span>
                        {countries_html}
                    </div>
                    {'<div class="book-desc">' + desc + '</div>' if desc else ''}
                    <div class="book-tags">
                        <span class="tag tag-lang">{lang}</span>
                        <span class="tag tag-region">{region_label}</span>
                        <span class="tag tag-year">{pub_date[:4] if pub_date else ''}</span>
                        <span class="tag tag-type">{type_label}</span>
                    </div>
                    <div class="book-actions">{actions}</div>
                </div>
            </div>
        </div>"""

    # ═══ بناء الصفحة ═══
    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 مرصد كتب الفساد | Corruption Books Observatory</title>
    <meta name="description" content="مرصد يومي مُحدَّث تلقائيًا لأحدث الكتب حول الفساد ومكافحته – العالم العربي وأفريقيا">
    <link rel="preconnect" href="https://books.google.com">
    <link rel="preconnect" href="https://covers.openlibrary.org">
    <style>
        :root {{
            --primary: #1a1a2e;
            --secondary: #16213e;
            --accent: #e94560;
            --accent2: #0f3460;
            --gold: #f0a500;
            --light: #f5f5f5;
            --white: #fff;
            --text: #333;
            --text-light: #666;
            --success: #27ae60;
            --warning: #f39c12;
            --shadow: 0 4px 15px rgba(0,0,0,0.08);
            --shadow-hover: 0 12px 35px rgba(0,0,0,0.18);
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',Tahoma,Arial,sans-serif; background:var(--light); color:var(--text); line-height:1.7; }}

        /* ── HEADER ── */
        header {{
            background: linear-gradient(135deg, var(--primary), var(--secondary) 50%, var(--accent2));
            color:var(--white); padding:50px 20px 40px; text-align:center;
            position:relative; overflow:hidden;
        }}
        header::before {{
            content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%;
            background: radial-gradient(circle, rgba(233,69,96,0.1), transparent 70%);
            animation: pulse 8s ease-in-out infinite;
        }}
        @keyframes pulse {{ 0%,100%{{transform:scale(1)}} 50%{{transform:scale(1.1)}} }}
        header h1 {{ font-size:2.3em; margin-bottom:8px; position:relative; z-index:1; }}
        header .subtitle {{ font-size:1.05em; opacity:0.9; max-width:700px; margin:0 auto 15px; position:relative; z-index:1; }}
        .header-badges {{ display:flex; justify-content:center; gap:10px; flex-wrap:wrap; position:relative; z-index:1; }}
        .badge {{ background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.3); padding:5px 14px; border-radius:20px; font-size:0.82em; }}
        .auto-badge {{ background:rgba(233,69,96,0.35); border-color:rgba(233,69,96,0.5); animation: glow 2s ease-in-out infinite alternate; }}
        @keyframes glow {{ from{{box-shadow:0 0 5px rgba(233,69,96,0.3)}} to{{box-shadow:0 0 15px rgba(233,69,96,0.6)}} }}

        /* ── CRITERIA ── */
        .criteria-bar {{
            background:var(--white); border-bottom:3px solid var(--accent);
            padding:14px 20px; display:flex; justify-content:center; gap:22px; flex-wrap:wrap;
        }}
        .criteria-item {{ display:flex; align-items:center; gap:6px; font-size:0.84em; font-weight:600; }}

        /* ── FILTERS ── */
        .filters {{
            background:var(--white); padding:15px 20px; text-align:center;
            position:sticky; top:0; z-index:100; box-shadow:0 2px 15px rgba(0,0,0,0.1);
        }}
        .filter-buttons {{ display:flex; justify-content:center; gap:8px; flex-wrap:wrap; margin-bottom:12px; }}
        .filter-btn {{
            padding:7px 18px; border:2px solid var(--accent2); background:transparent;
            color:var(--accent2); border-radius:25px; cursor:pointer;
            font-size:0.82em; font-weight:600; transition:all 0.3s; font-family:inherit;
        }}
        .filter-btn:hover, .filter-btn.active {{ background:var(--accent2); color:var(--white); }}
        .search-box {{ max-width:500px; margin:0 auto; position:relative; }}
        .search-box input {{
            width:100%; padding:10px 40px 10px 15px; border:2px solid #ddd; border-radius:25px;
            font-size:0.9em; font-family:inherit; direction:rtl; outline:none; transition:border-color 0.3s;
        }}
        .search-box input:focus {{ border-color:var(--accent); }}
        .search-box .search-icon {{ position:absolute; left:15px; top:50%; transform:translateY(-50%); font-size:1.1em; color:#999; }}

        /* ── MAIN ── */
        main {{ max-width:1300px; margin:0 auto; padding:25px 20px; }}

        /* ── STATS ── */
        .stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:12px; margin:25px 0; }}
        .stat-card {{ background:var(--white); border-radius:12px; padding:16px; text-align:center; box-shadow:var(--shadow); }}
        .stat-card .number {{ font-size:2em; font-weight:800; color:var(--accent); }}
        .stat-card .label {{ font-size:0.8em; color:var(--text-light); margin-top:2px; }}

        .section-title {{
            font-size:1.5em; color:var(--primary); margin:35px 0 18px;
            padding-bottom:8px; border-bottom:3px solid var(--accent);
        }}

        /* ═══════════════════════════════ */
        /* ── 🖼️ BOOK CARDS WITH COVERS ── */
        /* ═══════════════════════════════ */
        .books-grid {{
            display:grid;
            grid-template-columns:repeat(auto-fill, minmax(420px, 1fr));
            gap:20px; margin-bottom:35px;
        }}

        .book-card {{
            background:var(--white); border-radius:14px;
            box-shadow:var(--shadow); transition:all 0.35s ease;
            overflow:hidden; position:relative;
        }}
        .book-card:hover {{ box-shadow:var(--shadow-hover); transform:translateY(-4px); }}
        .book-card.hidden {{ display:none !important; }}

        .book-card.africa {{ border-top:4px solid var(--success); }}
        .book-card.arab {{ border-top:4px solid var(--accent); }}
        .book-card.global {{ border-top:4px solid var(--accent2); }}
        .book-card.french {{ border-top:4px solid var(--warning); }}

        .book-number {{
            position:absolute; top:12px; right:12px; z-index:5;
            background:var(--primary); color:var(--white);
            width:28px; height:28px; border-radius:50%;
            display:flex; align-items:center; justify-content:center;
            font-size:0.72em; font-weight:700;
        }}

        .book-inner {{
            display:flex; gap:0;
            min-height:220px;
        }}

        /* ── COVER ── */
        .cover-link {{
            display:block; flex-shrink:0;
            width:150px; min-height:220px;
            text-decoration:none; position:relative;
            overflow:hidden;
        }}

        .cover-wrapper {{
            width:100%; height:100%;
            position:relative; overflow:hidden;
            background:#e8e8e8;
        }}

        .book-cover {{
            width:100%; height:100%;
            object-fit:cover;
            transition: transform 0.4s ease, filter 0.3s;
            display:block;
        }}

        .cover-fallback {{
            object-fit:contain !important;
            padding:20px;
            background:linear-gradient(135deg, var(--primary), var(--accent2));
        }}

        .cover-overlay {{
            position:absolute; inset:0;
            background:rgba(15,52,96,0.75);
            display:flex; align-items:center; justify-content:center;
            opacity:0; transition:opacity 0.35s;
        }}

        .cover-overlay span {{
            color:var(--white); font-size:0.95em; font-weight:700;
            padding:8px 16px; border:2px solid var(--white); border-radius:25px;
            backdrop-filter:blur(3px);
        }}

        .cover-link:hover .book-cover {{ transform:scale(1.08); filter:brightness(0.8); }}
        .cover-link:hover .cover-overlay {{ opacity:1; }}

        /* ── DETAILS ── */
        .book-details {{
            flex:1; padding:18px 20px 15px;
            display:flex; flex-direction:column; gap:6px;
            overflow:hidden;
        }}

        .book-title {{
            font-size:1.02em; font-weight:700; line-height:1.35;
        }}
        .book-title a {{
            color:var(--primary); text-decoration:none;
            transition:color 0.2s;
        }}
        .book-title a:hover {{ color:var(--accent); }}

        .book-meta {{ display:flex; flex-direction:column; gap:3px; }}
        .meta-item {{ font-size:0.8em; color:var(--text-light); }}

        .book-desc {{
            font-size:0.82em; color:var(--text); line-height:1.55;
            background:#f8f9fa; padding:8px 10px; border-radius:8px;
            max-height:80px; overflow:hidden;
            position:relative;
        }}
        .book-desc::after {{
            content:''; position:absolute; bottom:0; left:0; right:0;
            height:25px; background:linear-gradient(transparent, #f8f9fa);
        }}

        .book-tags {{ display:flex; gap:5px; flex-wrap:wrap; margin-top:auto; }}
        .tag {{ font-size:0.68em; padding:2px 8px; border-radius:12px; font-weight:600; white-space:nowrap; }}
        .tag-lang {{ background:#e8f4fd; color:#1976d2; }}
        .tag-region {{ background:#e8f5e9; color:#2e7d32; }}
        .tag-year {{ background:#fff3e0; color:#e65100; }}
        .tag-type {{ background:#f3e5f5; color:#7b1fa2; }}

        /* ── ACTION BUTTONS ── */
        .book-actions {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }}
        .action-btn {{
            font-size:0.75em; padding:4px 12px; border-radius:15px;
            text-decoration:none; font-weight:600; font-family:inherit;
            transition:all 0.3s; display:inline-flex; align-items:center; gap:4px;
        }}
        .info-btn {{
            background:var(--accent2); color:var(--white);
        }}
        .info-btn:hover {{ background:var(--primary); }}
        .buy-btn {{
            background:var(--success); color:var(--white);
        }}
        .buy-btn:hover {{ background:#219a52; }}
        .preview-btn {{
            background:var(--warning); color:var(--white);
        }}
        .preview-btn:hover {{ background:#e08e0b; }}

        /* ── REPORTS TABLE ── */
        .reports-table {{
            width:100%; border-collapse:collapse; background:var(--white);
            border-radius:12px; overflow:hidden; box-shadow:var(--shadow); margin-bottom:35px;
        }}
        .reports-table th {{ background:var(--primary); color:var(--white); padding:12px; text-align:right; font-size:0.85em; }}
        .reports-table td {{ padding:10px 12px; border-bottom:1px solid #eee; font-size:0.83em; }}
        .reports-table tr:hover {{ background:#f8f9fa; }}
        .reports-table a {{ color:var(--accent2); text-decoration:none; font-weight:600; }}

        /* ── RESOURCES ── */
        .resources-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:12px; margin:18px 0 35px; }}
        .resource-card {{
            background:var(--white); border-radius:10px; padding:16px;
            box-shadow:var(--shadow); text-align:center; transition:all 0.3s;
        }}
        .resource-card:hover {{ box-shadow:var(--shadow-hover); transform:translateY(-2px); }}
        .resource-card .r-icon {{ font-size:1.8em; margin-bottom:6px; }}
        .resource-card h4 {{ font-size:0.88em; color:var(--primary); }}
        .resource-card p {{ font-size:0.76em; color:var(--text-light); margin:4px 0 8px; }}
        .resource-card a {{ color:var(--accent); text-decoration:none; font-weight:600; font-size:0.82em; }}

        /* ── UPDATE LOG ── */
        .update-log {{
            background:linear-gradient(135deg,#1a1a2e,#16213e); color:var(--white);
            border-radius:12px; padding:25px; margin:25px 0;
        }}
        .update-log h3 {{ margin-bottom:12px; color:var(--gold); }}
        .log-item {{ padding:5px 0; font-size:0.85em; opacity:0.9; border-bottom:1px solid rgba(255,255,255,0.08); }}

        /* ── FOOTER ── */
        footer {{
            background:var(--primary); color:rgba(255,255,255,0.7);
            text-align:center; padding:25px; font-size:0.82em;
        }}
        footer a {{ color:var(--gold); text-decoration:none; }}

        .no-results {{ text-align:center; padding:40px; color:var(--text-light); font-size:1.1em; display:none; }}

        /* ── RESPONSIVE ── */
        @media (max-width:768px) {{
            header h1 {{ font-size:1.5em; }}
            .books-grid {{ grid-template-columns:1fr; }}
            .book-inner {{ flex-direction:column; }}
            .cover-link {{ width:100%; min-height:200px; max-height:280px; }}
            .book-cover {{ height:250px; }}
        }}
        @media (max-width:500px) {{
            .books-grid {{ grid-template-columns:1fr; }}
            .cover-link {{ min-height:180px; }}
        }}
    </style>
</head>
<body>

    <header>
        <h1>📚 مرصد كتب الفساد</h1>
        <p class="subtitle">الكتب الحديثة حول الفساد ومكافحته – العالم العربي · أفريقيا · العالم</p>
        <div class="header-badges">
            <span class="badge auto-badge" id="updateBadge">🤖 تحديث يومي تلقائي</span>
            <span class="badge">📅 آخر {VALIDITY_MONTHS} شهرًا</span>
            <span class="badge">🗣️ عربي · English · Français</span>
            <span class="badge">❌ بدون خيال</span>
            <span class="badge">📆 {today_str}</span>
        </div>
    </header>

    <div class="criteria-bar">
        <div class="criteria-item"><span>📅</span><span>آخر {VALIDITY_MONTHS} شهرًا</span></div>
        <div class="criteria-item"><span>📖</span><span>غير خيالي</span></div>
        <div class="criteria-item"><span>🌍</span><span>أولوية: عربي + أفريقي</span></div>
        <div class="criteria-item"><span>🤖</span><span>تحديث يومي</span></div>
        <div class="criteria-item"><span>🖼️</span><span>أغلفة + روابط مباشرة</span></div>
    </div>

    <div class="filters">
        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterBooks('all')">📚 الكل ({total})</button>
            <button class="filter-btn" onclick="filterBooks('africa')">🌍 أفريقيا ({len(by_region['africa'])})</button>
            <button class="filter-btn" onclick="filterBooks('arab')">🏛️ عربي ({len(by_region['arab'])})</button>
            <button class="filter-btn" onclick="filterBooks('global')">🌐 عالمي ({len(by_region['global'])})</button>
            <button class="filter-btn" onclick="filterBooks('french')">🇫🇷 فرنسي ({len(by_region['french'])})</button>
            <button class="filter-btn" onclick="filterBooks('report')">📊 تقارير ({len(reports)})</button>
        </div>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 ابحث بالعنوان أو المؤلف أو الناشر..." oninput="searchBooks(this.value)">
        </div>
    </div>

    <main>
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{total}</div><div class="label">📚 كتاب</div></div>
            <div class="stat-card"><div class="number">{len(by_region['africa'])}</div><div class="label">🌍 أفريقيا</div></div>
            <div class="stat-card"><div class="number">{len(by_region['arab'])}</div><div class="label">🏛️ عربي</div></div>
            <div class="stat-card"><div class="number">{len(by_region['global'])+len(by_region['french'])}</div><div class="label">🌐 عالمي</div></div>
            <div class="stat-card"><div class="number">{len(reports)}</div><div class="label">📊 تقارير</div></div>
        </div>

        <div id="noResults" class="no-results">😔 لا توجد نتائج مطابقة</div>
"""

    # ═══ أقسام الكتب ═══
    sections = [
        ("africa", "🌍 كتب عن الفساد في أفريقيا", by_region["africa"]),
        ("arab", "🏛️ كتب عن الفساد في العالم العربي", by_region["arab"]),
        ("global", "🌐 كتب بمنظور عالمي / مقارن", by_region["global"]),
        ("french", "🇫🇷 كتب بالفرنسية", by_region["french"]),
    ]

    counter = 1
    for rid, title, bks in sections:
        if not bks:
            continue
        html += f'\n        <h2 class="section-title section-{rid}">{title}</h2>\n        <div class="books-grid">'
        for b in bks:
            html += card(b, counter, rid)
            counter += 1
        html += '\n        </div>'

    # ═══ التقارير ═══
    if reports:
        html += '\n        <h2 class="section-title section-report">📊 تقارير مؤسسية</h2>\n        <table class="reports-table"><thead><tr><th>#</th><th>التقرير</th><th>الجهة</th><th>التاريخ</th><th>رابط</th></tr></thead><tbody>'
        for i, r in enumerate(reports, 1):
            link = r.get("info_url", "") or r.get("link", "")
            lnk = f'<a href="{link}" target="_blank">↗ اطّلع عليه</a>' if link else "—"
            html += f'\n            <tr class="book-card report" data-category="report" data-searchable="{r.get("title","").lower()}"><td>T{i}</td><td><strong>{r.get("title","")}</strong></td><td>{r.get("publisher","")}</td><td>{r.get("published_date","")}</td><td>{lnk}</td></tr>'
        html += '\n        </tbody></table>'

    # ═══ الموارد ═══
    html += f"""
        <h2 class="section-title">🔗 موارد دائمة</h2>
        <div class="resources-grid">
            <div class="resource-card"><div class="r-icon">🌐</div><h4>Transparency International</h4><p>مؤشر مدركات الفساد</p><a href="https://www.transparency.org" target="_blank">transparency.org ↗</a></div>
            <div class="resource-card"><div class="r-icon">🇺🇳</div><h4>UNODC – UNCAC</h4><p>اتفاقية مكافحة الفساد</p><a href="https://www.unodc.org/corruption/" target="_blank">unodc.org ↗</a></div>
            <div class="resource-card"><div class="r-icon">🌍</div><h4>Mo Ibrahim Foundation</h4><p>الحوكمة الأفريقية</p><a href="https://mo.ibrahim.foundation/iiag" target="_blank">mo.ibrahim.foundation ↗</a></div>
            <div class="resource-card"><div class="r-icon">🏦</div><h4>World Bank – WGI</h4><p>مؤشرات الحوكمة</p><a href="https://info.worldbank.org/governance/wgi/" target="_blank">worldbank.org ↗</a></div>
            <div class="resource-card"><div class="r-icon">🤝</div><h4>UNCAC Coalition</h4><p>ائتلاف المجتمع المدني</p><a href="https://uncaccoalition.org/" target="_blank">uncaccoalition.org ↗</a></div>
            <div class="resource-card"><div class="r-icon">📚</div><h4>Routledge RCACS</h4><p>سلسلة دراسات الفساد</p><a href="https://www.routledge.com" target="_blank">routledge.com ↗</a></div>
        </div>

        <div class="update-log">
            <h3>🤖 سجل التحديث</h3>
            <div class="log-item">📅 آخر تحديث: <strong>{today_str}</strong></div>
            <div class="log-item">📚 الكتب الحالية: <strong>{total}</strong></div>
            <div class="log-item">🆕 جديدة: <strong>{stats.get('new_books',0)}</strong></div>
            <div class="log-item">🗑️ مؤرشفة: <strong>{stats.get('archived',0)}</strong></div>
            <div class="log-item">🖼️ أغلفة محلولة: <strong>{stats.get('covers_found',0)}</strong></div>
            <div class="log-item">🔌 المصادر: Google Books · Open Library · CrossRef</div>
        </div>
    </main>

    <footer>
        <p>📚 مرصد كتب الفساد | Corruption Books Observatory<br>
        مفتوح المصدر – MIT – تحديث يومي تلقائي – 🤖 {today_str}</p>
    </footer>

    <script>
        function filterBooks(cat) {{
            const cards = document.querySelectorAll('.book-card');
            const btns = document.querySelectorAll('.filter-btn');
            const nr = document.getElementById('noResults');
            btns.forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            let vis = 0;
            cards.forEach(c => {{
                const show = cat === 'all' || c.dataset.category === cat;
                c.classList.toggle('hidden', !show);
                if (show) vis++;
            }});
            document.querySelectorAll('.section-title').forEach(s => {{
                s.style.display = cat === 'all' || s.classList.contains('section-' + cat) ? '' : 'none';
            }});
            document.querySelectorAll('.books-grid').forEach(g => {{
                const hasVisible = [...g.children].some(c => !c.classList.contains('hidden'));
                g.style.display = hasVisible ? '' : 'none';
            }});
            nr.style.display = vis === 0 ? 'block' : 'none';
            document.getElementById('searchInput').value = '';
        }}

        function searchBooks(q) {{
            q = q.toLowerCase().trim();
            const cards = document.querySelectorAll('.book-card');
            const nr = document.getElementById('noResults');
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            document.querySelector('.filter-btn').classList.add('active');
            document.querySelectorAll('.section-title').forEach(s => s.style.display = '');
            document.querySelectorAll('.books-grid').forEach(g => g.style.display = '');
            let vis = 0;
            cards.forEach(c => {{
                const text = (c.dataset.searchable || c.textContent).toLowerCase();
                const show = !q || text.includes(q);
                c.classList.toggle('hidden', !show);
                if (show) vis++;
            }});
            nr.style.display = vis === 0 ? 'block' : 'none';
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            const badge = document.getElementById('updateBadge');
            if (badge) {{
                const last = new Date('{today_str}');
                const diff = Math.floor((new Date() - last) / 36e5);
                badge.textContent = diff < 24 ? '🤖 تم التحديث اليوم' :
                    diff < 48 ? '🤖 تم التحديث أمس' : '🤖 آخر تحديث: منذ ' + Math.floor(diff/24) + ' أيام';
            }}
        }});
    </script>
</body>
</html>"""

    return html
