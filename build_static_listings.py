#!/usr/bin/env python3
"""
build_static_listings.py

Reads listings.csv and injects pre-rendered ("SSR") listing cards into each
area/local/*.html page, so the raw HTML contains real listing content
(project name, price, zone, etc.) instead of just "Loading listings...".

Also injects a pre-rendered ("SSR") copy of the area directory into
kawasan.html, so the 25 area cards (and their links to area/local/*.html)
are present in the raw HTML instead of only existing inside a client-side
<script> that built them at runtime.

This is progressive enhancement, not a replacement:
- Your existing client-side JS (fetch + applyFilters, and kawasan.html's
  renderAreas()) still runs exactly as before and takes over once loaded,
  giving live filtering/search.
- Search engines and AI crawlers that don't execute JS now see real content
  on first load instead of an empty placeholder.

Safe to re-run any time listings.csv changes — it replaces only the content
between the SSR markers, it does not duplicate on repeat runs.

The AREAS list below is the single source of truth for the area directory:
each run re-renders both the static SSR cards AND the inline `const AREAS`
JS array inside kawasan.html from this one list, so the two can never drift
out of sync. To add/remove/edit an area, edit AREAS here and re-run — do not
hand-edit the AREAS array inside kawasan.html anymore.

Usage:
    python3 build_static_listings.py
"""

import csv
import html
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent
LISTINGS_CSV = ROOT / "listings.csv"
AREA_DIR = ROOT / "area" / "local"
KAWASAN_PATH = ROOT / "kawasan.html"
HOMEPAGE_PATH = ROOT / "index.html"
WA_BASE = "https://wa.me/60125459182?text="

SSR_START = "<!--SSR_START-->"
SSR_END = "<!--SSR_END-->"


def wa(text: str) -> str:
    return WA_BASE + urllib.parse.quote(text)


def fmt_price(price) -> str:
    try:
        n = float(str(price).replace(",", ""))
        return "RM " + f"{int(n):,}"
    except (ValueError, TypeError):
        return "RM " + str(price)


def to_slug(*parts) -> str:
    joined = "-".join(str(p) for p in parts if p)
    slug = re.sub(r"[^a-z0-9]+", "-", joined.lower())
    return slug.strip("-")


def move_in_text(val: str) -> str:
    v = (val or "").strip()
    if not v or v == "-":
        return ""
    return f"\U0001F5D3 Move-in: {esc(v)}"


def coa_badge(code: str) -> str:
    if not code:
        return ""
    return f'<span class="card-badge badge-coa">{esc(code)}</span>'


def esc(s) -> str:
    return html.escape(str(s or ""), quote=False)


def card_image(r: dict) -> str:
    raw = (r.get("image") or "").strip()
    imgs = []
    if raw and raw != "-":
        base = ""
        for p in raw.split("|"):
            p = p.strip()
            if not p:
                continue
            if re.match(r"^https?://", p, re.I):
                base = p.rsplit("/", 1)[0] + "/"
                imgs.append(p)
            else:
                imgs.append(base + p if base else p)
    if not imgs:
        imgs = ["/images/update.png"]

    nav = ""
    if len(imgs) > 1:
        dots = "".join(
            f'<span class="card-img-dot{" active" if i == 0 else ""}"></span>'
            for i in range(len(imgs))
        )
        nav = (
            '<button type="button" class="card-img-nav prev" '
            'onclick="cardImgNav(event,this,-1)" aria-label="Previous photo">‹</button>'
            '<button type="button" class="card-img-nav next" '
            'onclick="cardImgNav(event,this,1)" aria-label="Next photo">›</button>'
            f'<div class="card-img-dots">{dots}</div>'
        )

    imgs_attr = esc("|".join(imgs))
    first = html.escape(imgs[0], quote=True)
    alt = html.escape(r.get("project_name", ""), quote=True)
    return (
        f'<div class="card-image-wrap" data-images="{imgs_attr}" data-index="0">'
        f'<img src="{first}" alt="{alt}" class="card-image" loading="lazy" '
        f'onerror="this.onerror=null;this.src=\'/images/update.png\';" '
        f'onclick="openLightbox(event,this)">{nav}'
        f"</div>"
    )


def pills_html(items) -> str:
    return "".join(f'<span class="pill">{p}</span>' for p in items if p)


def size_pill(r: dict) -> str:
    v = (r.get("size") or "").strip()
    if not v or v == "-":
        return ""
    try:
        return f"{int(float(v)):,} sqft"
    except ValueError:
        return ""


def unit_card(r: dict) -> str:
    pills = pills_html([
        f"\U0001F6CF {esc(r['bed'])} bed" if r.get("bed") else "",
        f"\U0001F6BF {esc(r['bath'])} bath" if r.get("bath") else "",
        size_pill(r),
        esc(r.get("furnishing")),
        esc(r.get("type")),
        move_in_text(r.get("move_in_date")),
    ])
    name = esc(r.get("project_name"))
    zone = esc(r.get("zone"))
    wa_text = r.get("wa_text") or f"Hi Hani, I'm interested in {r.get('project_name')}, {r.get('zone')}."
    anchors = f'<div class="card-anchors">{esc(r.get("anchors"))}</div>' if r.get("anchors") else ""
    return f'''<div class="card" id="{to_slug(r.get('project_name'), r.get('bed'), r.get('price'))}">
    {card_image(r)}
    <div class="card-body">
      <div><span class="card-badge badge-unit">Unit Rental</span>{coa_badge(r.get('code'))}</div>
      <div><div class="card-name">{name}</div><div class="card-zone">{zone}</div></div>
      <div class="card-price">{fmt_price(r.get('price'))}<span> / month</span></div>
      <div class="card-pills">{pills}</div>
      {anchors}
      <a href="{wa(wa_text)}" class="card-cta" target="_blank" rel="noopener noreferrer">\U0001F4AC Enquire on WhatsApp</a>
    </div>
  </div>'''


def room_card(r: dict) -> str:
    pills = pills_html([
        esc(r.get("room_type")),
        esc(r.get("bath_type")),
        esc(r.get("furnishing")),
        move_in_text(r.get("move_in_date")),
    ])
    name = esc(r.get("project_name"))
    zone = esc(r.get("zone"))
    wa_text = r.get("wa_text") or f"Hi Hani, I'm interested in a room at {r.get('project_name')}, {r.get('zone')}."
    anchors = f'<div class="card-anchors">{esc(r.get("anchors"))}</div>' if r.get("anchors") else ""
    return f'''<div class="card" id="{to_slug(r.get('project_name'), r.get('room_type'), r.get('price'))}">
    {card_image(r)}
    <div class="card-body">
      <div><span class="card-badge badge-room">Room Rental</span>{coa_badge(r.get('code'))}</div>
      <div><div class="card-name">{name}</div><div class="card-zone">{zone}</div></div>
      <div class="card-price">{fmt_price(r.get('price'))}<span> / month</span></div>
      <div class="card-pills">{pills}</div>
      {anchors}
      <a href="{wa(wa_text)}" class="card-cta" target="_blank" rel="noopener noreferrer">\U0001F4AC Enquire on WhatsApp</a>
    </div>
  </div>'''


def subsale_card(r: dict) -> str:
    pills = pills_html([
        f"\U0001F6CF {esc(r['bed'])} bed" if r.get("bed") else "",
        f"\U0001F6BF {esc(r['bath'])} bath" if r.get("bath") else "",
        size_pill(r),
        esc(r.get("tenure")),
        esc(r.get("type")),
    ])
    name = esc(r.get("project_name"))
    zone = esc(r.get("zone"))
    wa_text = r.get("wa_text") or f"Hi Hani, I'm interested in the subsale unit at {r.get('project_name')}, {r.get('zone')}."
    anchors = f'<div class="card-anchors">{esc(r.get("anchors"))}</div>' if r.get("anchors") else ""
    inst = ""
    if r.get("installment"):
        try:
            inst_val = f"{int(float(str(r['installment']).replace(',', ''))):,}"
            inst = (f'<div style="font-size:12px;color:#7a7268;margin-top:-6px;">Est. '
                    f'<strong style="color:#2a5c3a;">RM {inst_val}</strong>/mo instalment</div>')
        except ValueError:
            pass
    return f'''<div class="card" id="{to_slug(r.get('project_name'), r.get('bed'), r.get('price'))}">
    {card_image(r)}
    <div class="card-body">
      <div><span class="card-badge badge-subsale">Subsale</span>{coa_badge(r.get('code'))}</div>
      <div><div class="card-name">{name}</div><div class="card-zone">{zone}</div></div>
      <div class="card-price">{fmt_price(r.get('price'))}</div>
      {inst}
      <div class="card-pills">{pills}</div>
      {anchors}
      <a href="{wa(wa_text)}" class="card-cta" target="_blank" rel="noopener noreferrer">\U0001F4AC Enquire on WhatsApp</a>
    </div>
  </div>'''


def lelong_card(r: dict) -> str:
    pills = pills_html([
        f"\U0001F6CF {esc(r['bed'])} bed" if r.get("bed") else "",
        f"\U0001F6BF {esc(r['bath'])} bath" if r.get("bath") else "",
        size_pill(r),
        esc(r.get("tenure")),
        esc(r.get("type")),
    ])
    name = esc(r.get("project_name"))
    zone = esc(r.get("zone"))
    lelong_date = (r.get("Lelong date") or "").strip()
    auction_pill = (
        f'<div class="card-pills"><span class="pill">\U0001F528 Auction: {esc(lelong_date)}</span></div>'
        if lelong_date and lelong_date != "-" else ""
    )
    wa_text = r.get("wa_text") or f"Hi Hani, I'm interested in the lelong/auction unit at {r.get('project_name')}, {r.get('zone')}."
    anchors = f'<div class="card-anchors">{esc(r.get("anchors"))}</div>' if r.get("anchors") else ""
    inst = ""
    if r.get("installment"):
        try:
            inst_val = f"{int(float(str(r['installment']).replace(',', ''))):,}"
            inst = (f'<div style="font-size:12px;color:#7a7268;margin-top:-6px;">Est. '
                    f'<strong style="color:#2a5c3a;">RM {inst_val}</strong>/mo instalment</div>')
        except ValueError:
            pass
    return f'''<div class="card" id="{to_slug(r.get('project_name'), r.get('bed'), r.get('price'))}">
    {card_image(r)}
    <div class="card-body">
      <div><span class="card-badge badge-lelong">Lelong</span>{coa_badge(r.get('code'))}</div>
      <div><div class="card-name">{name}</div><div class="card-zone">{zone}</div></div>
      <div class="card-price">{fmt_price(r.get('price'))}</div>
      {inst}
      <div class="card-pills">{pills}</div>
      {auction_pill}
      {anchors}
      <a href="{wa(wa_text)}" class="card-cta" target="_blank" rel="noopener noreferrer">\U0001F4AC Enquire on WhatsApp</a>
    </div>
  </div>'''


def empty_html(msg: str) -> str:
    return f'<div class="empty">{msg}</div>'


def load_listings():
    with open(LISTINGS_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def inject_grid(html_text: str, grid_id: str, cards_markup: str) -> str:
    """Replace content inside <div class="listing-grid" id="{grid_id}">...</div>
    with SSR-marked static cards. Works whether or not SSR markers already exist."""
    marker_pattern = re.compile(
        rf'(<div class="listing-grid" id="{grid_id}">){SSR_START}.*?{SSR_END}(</div>)',
        re.DOTALL,
    )
    loading_pattern = re.compile(
        rf'(<div class="listing-grid" id="{grid_id}"><div class="loading">Loading listings…</div>)(</div>)'
    )
    replacement = rf'\g<1>{SSR_START}{cards_markup}{SSR_END}\g<2>'

    if marker_pattern.search(html_text):
        return marker_pattern.sub(lambda m: f'<div class="listing-grid" id="{grid_id}">{SSR_START}{cards_markup}{SSR_END}</div>', html_text)
    if loading_pattern.search(html_text):
        return loading_pattern.sub(lambda m: f'<div class="listing-grid" id="{grid_id}">{SSR_START}{cards_markup}{SSR_END}</div>', html_text)
    print(f"    (warning: grid#{grid_id} not found in expected form, skipped)")
    return html_text


def process_area_file(path: Path, all_rows):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"const AREA\s*=\s*'([^']*)'", text)
    if not m:
        print(f"  skip {path.name}: no AREA constant found")
        return
    area = m.group(1)

    # Optional ZONE constant lets a page target a specific sub-area/township
    # within a broader CSV "area" value (e.g. Setia Alam is a "zone" inside
    # the "Shah Alam" area, not its own top-level area). When present, only
    # rows matching both area and zone are pulled into this page.
    zm = re.search(r"const ZONE\s*=\s*'([^']*)'", text)
    zone = zm.group(1) if zm else None

    filtered = [
        r for r in all_rows
        if r.get("area") == area
        and (zone is None or r.get("zone") == zone)
        and (r.get("status") in ("-", "", None))
    ]
    units = [r for r in filtered if r.get("listing_type") == "rental"]
    rooms = [r for r in filtered if r.get("listing_type") == "room"]
    subsales = [r for r in filtered if r.get("listing_type") == "subsale"]
    lelongs = [r for r in filtered if r.get("listing_type") == "lelong"]

    unit_html = "".join(unit_card(r) for r in units) if units else empty_html("No unit rentals available right now.")
    room_html = "".join(room_card(r) for r in rooms) if rooms else empty_html("No room rentals available right now.")
    subsale_html = "".join(subsale_card(r) for r in subsales) if subsales else empty_html("No subsale listings available right now.")
    lelong_html = "".join(lelong_card(r) for r in lelongs) if lelongs else empty_html("No lelong/auction listings available right now.")

    text = inject_grid(text, "grid-unit", unit_html)
    text = inject_grid(text, "grid-room-tab", room_html)
    text = inject_grid(text, "grid-subsale", subsale_html)
    text = inject_grid(text, "grid-lelong", lelong_html)

    path.write_text(text, encoding="utf-8")
    print(f"  {path.name}: {area} -> {len(units)} rental, {len(rooms)} room, {len(subsales)} subsale, {len(lelongs)} lelong")


# ---------------------------------------------------------------------------
# Area directory (kawasan.html)
#
# AREAS is the single source of truth for the "Areas We Cover" directory.
# Each run re-renders both:
#   1. the static SSR cards inside <div id="area-results"> in kawasan.html
#   2. the inline `const AREAS = [...]` JS array inside the same file
# from this one list, so the crawlable static HTML and the client-side
# renderAreas() script can never drift apart. Edit AREAS here, not in the
# HTML file.
# ---------------------------------------------------------------------------

AREAS = [
    {"slug": "shah-alam", "name": "Shah Alam", "region": "Selangor", "popular": True, "tag": "UiTM, Blue Mosque, PKNS"},
    {"slug": "setia-alam", "name": "Setia Alam", "region": "Selangor", "tag": "Setia City Mall, Setia Eco Park, NKVE"},
    {"slug": "petaling-jaya", "name": "Petaling Jaya / Damansara", "region": "Selangor", "popular": True, "tag": "1 Utama, IKEA Damansara, The Curve"},
    {"slug": "puchong", "name": "Puchong", "region": "Selangor", "popular": True, "tag": "IOI Mall, Setiawalk, PFCC"},
    {"slug": "subang-jaya", "name": "Subang Jaya", "region": "Selangor", "popular": True, "tag": "Sunway Pyramid, Empire, SS15"},
    {"slug": "klang", "name": "Klang", "region": "Selangor", "popular": True, "tag": "Bandar Botanic, AEON Bukit Tinggi"},
    {"slug": "kajang-bangi", "name": "Kajang & Bangi", "region": "Selangor", "tag": "MRT Kajang, UKM, IOI Mall Bangi"},
    {"slug": "semenyih", "name": "Semenyih", "region": "Selangor", "tag": "UNITEN, EcoHill Mall"},
    {"slug": "seri-kembangan", "name": "Seri Kembangan", "region": "Selangor", "tag": "The Mines, MRT Serdang Jaya"},
    {"slug": "cyberjaya-putrajaya", "name": "Cyberjaya / Putrajaya", "region": "Selangor", "tag": "MMU, IOI City Mall, KLIA Transit"},
    {"slug": "sepang", "name": "Sepang / Banting / Dengkil", "region": "Selangor", "tag": "KLIA, klia2, Sepang Circuit"},
    {"slug": "bandar-saujana-putra", "name": "Bandar Saujana Putra", "region": "Selangor", "tag": "Cyberjaya, Putra Heights, ELITE Hwy"},
    {"slug": "rimbayu-tpg", "name": "Rimbayu / TPG", "region": "Selangor", "tag": "Central Park, Kota Kemuning"},
    {"slug": "puncak-alam", "name": "Puncak Alam", "region": "Selangor", "tag": "UiTM Puncak Alam, AEON Bukit Raja"},
    {"slug": "rawang", "name": "Rawang", "region": "Selangor", "tag": "KTM Rawang, Templer Park"},
    {"slug": "sungai-buloh", "name": "Sungai Buloh", "region": "Selangor", "tag": "MRT/KTM Interchange, Sierramas"},
    {"slug": "kuala-lumpur", "name": "Kuala Lumpur", "region": "Kuala Lumpur", "popular": True, "tag": "KLCC, Bukit Bintang, Mid Valley"},
    {"slug": "bukit-jalil", "name": "Bukit Jalil", "region": "Kuala Lumpur", "popular": True, "tag": "Pavilion, National Stadium, LRT"},
    {"slug": "cheras", "name": "Cheras", "region": "Kuala Lumpur", "popular": True, "tag": "Sunway Velocity, IKEA, Taman Connaught"},
    {"slug": "ampang", "name": "Ampang", "region": "Kuala Lumpur", "popular": True, "tag": "Jalan Ampang, AKLEH, KL Golden Triangle"},
    {"slug": "kepong", "name": "Kepong", "region": "Kuala Lumpur", "popular": True, "tag": "Desa ParkCity, KTM Kepong"},
    {"slug": "setapak", "name": "Setapak", "region": "Kuala Lumpur", "tag": "UTAR, Wangsa Walk Mall"},
    {"slug": "sentul", "name": "Sentul", "region": "Kuala Lumpur", "tag": "Sentul Timur LRT, KL Sentral"},
    {"slug": "selayang", "name": "Selayang", "region": "Kuala Lumpur", "tag": "Batu Caves, Selayang Hospital"},
    {"slug": "nilai", "name": "Nilai", "region": "Negeri Sembilan", "tag": "USIM, INTI University, AEON Nilai"},
]

REGION_ORDER = ["Selangor", "Kuala Lumpur", "Negeri Sembilan"]


def area_card_html(a: dict) -> str:
    """Mirrors kawasan.html's client-side cardHtml() function exactly, so the
    SSR markup and the JS-rendered markup are visually identical."""
    popular = bool(a.get("popular"))
    popular_class = " popular" if popular else ""
    badge = '<span class="badge-popular">Popular</span>' if popular else ""
    name = html.escape(a["name"], quote=True)
    tag = html.escape(a["tag"], quote=False)
    slug = a["slug"]
    return (
        f'<a class="area-card{popular_class}" href="area/local/{slug}.html">'
        f'<img class="area-card-img" src="/images/areas/{slug}.webp" alt="{name}" '
        f'loading="lazy" width="112" height="112" onerror="this.style.display=\'none\'">'
        f'<div class="area-card-body">'
        f'<div class="area-card-name">{name}{badge}</div>'
        f'<div class="area-card-tag">{tag}</div>'
        f'</div></a>'
    )


def render_area_directory_html() -> str:
    """Mirrors kawasan.html's client-side renderAreas() function: groups
    AREAS by region (in REGION_ORDER) and renders each region's label + grid."""
    blocks = []
    for region in REGION_ORDER:
        items = [a for a in AREAS if a["region"] == region]
        if not items:
            continue
        count_label = f'{len(items)} area{"s" if len(items) != 1 else ""}'
        cards = "".join(area_card_html(a) for a in items)
        blocks.append(
            f'<div class="region-label"><span>{html.escape(region)}</span>'
            f'<span class="region-count">{count_label}</span></div>'
            f'<div class="area-grid">{cards}</div>'
        )
    return "".join(blocks)


def inject_area_directory(html_text: str, cards_markup: str) -> str:
    """Same technique as inject_grid(): replace whatever is inside
    <div id="area-results">...</div> with SSR-marked static area cards.
    Works whether the div is still empty (first run) or already has SSR
    markers from a previous run."""
    marker_pattern = re.compile(
        rf'(<div id="area-results">){SSR_START}.*?{SSR_END}(</div>)',
        re.DOTALL,
    )
    empty_pattern = re.compile(r'(<div id="area-results">)(</div>)')
    replacement_html = f'{SSR_START}{cards_markup}{SSR_END}'

    if marker_pattern.search(html_text):
        return marker_pattern.sub(lambda m: f'<div id="area-results">{replacement_html}</div>', html_text)
    if empty_pattern.search(html_text):
        return empty_pattern.sub(lambda m: f'<div id="area-results">{replacement_html}</div>', html_text)
    print("    (warning: #area-results div not found in expected form, skipped)")
    return html_text


def _js_str(s: str) -> str:
    """Escape a string for embedding inside a single-quoted JS string literal."""
    return s.replace("\\", "\\\\").replace("'", "\\'")


def js_areas_literal() -> str:
    """Re-serialize AREAS as the `const AREAS = [...]` JS array literal, in
    the same shape kawasan.html's renderAreas()/cardHtml() already expect,
    so the inline <script> stays byte-for-byte in sync with the AREAS list
    above -- one source of truth, no hand-editing the JS array anymore."""
    lines = ["const AREAS = ["]
    for a in AREAS:
        parts = [
            f"slug: '{_js_str(a['slug'])}'",
            f"name: '{_js_str(a['name'])}'",
            f"region: '{_js_str(a['region'])}'",
        ]
        if a.get("popular"):
            parts.append("popular: true")
        parts.append(f"tag: '{_js_str(a['tag'])}'")
        lines.append("  { " + ", ".join(parts) + " },")
    lines.append("];")
    return "\n".join(lines)


def process_kawasan_page():
    if not KAWASAN_PATH.exists():
        print(f"  skip {KAWASAN_PATH.name}: not found")
        return

    text = KAWASAN_PATH.read_text(encoding="utf-8")

    directory_html = render_area_directory_html()
    text = inject_area_directory(text, directory_html)

    js_pattern = re.compile(r"const AREAS\s*=\s*\[.*?\];", re.DOTALL)
    text, n = js_pattern.subn(lambda m: js_areas_literal(), text, count=1)
    if n == 0:
        print("    (warning: const AREAS array not found in kawasan.html, JS copy not synced)")

    KAWASAN_PATH.write_text(text, encoding="utf-8")
    print(f"  {KAWASAN_PATH.name}: {len(AREAS)} areas injected as static HTML across {len([r for r in REGION_ORDER if any(a['region'] == r for a in AREAS)])} regions")


def sync_homepage_area_count():
    """Keeps index.html's 'View all N areas we cover' link text in sync with
    len(AREAS). This is the line that drifted stale before (it said 26 while
    AREAS only had 25 entries) -- deriving it from AREAS here means it can't
    go stale again, whatever the count changes to."""
    if not HOMEPAGE_PATH.exists():
        print(f"  skip {HOMEPAGE_PATH.name}: not found")
        return

    text = HOMEPAGE_PATH.read_text(encoding="utf-8")
    pattern = re.compile(r"View all \d+ areas? we cover")
    label = f"View all {len(AREAS)} area{'s' if len(AREAS) != 1 else ''} we cover"
    new_text, n = pattern.subn(label, text)

    if n == 0:
        print("    (warning: 'View all N areas we cover' text not found in index.html, skipped)")
        return
    if new_text == text:
        print(f"  {HOMEPAGE_PATH.name}: area count link already correct ({len(AREAS)})")
        return

    HOMEPAGE_PATH.write_text(new_text, encoding="utf-8")
    print(f"  {HOMEPAGE_PATH.name}: area count link updated to {len(AREAS)}")


SITEMAP_PATH = ROOT / "sitemap.xml"
SITE_BASE = "https://haniproperties.com"

# Core (non-area) pages that always belong in the sitemap.
# path relative to site root, changefreq, priority
CORE_PAGES = [
    ("/", "weekly", "1.0"),
    ("/kawasan.html", "weekly", "0.9"),
    ("/investor-corner.html", "weekly", "0.9"),
    ("/offerings.html", "monthly", "0.8"),
    ("/simple.html", "monthly", "0.8"),
    ("/calculator.html", "monthly", "0.8"),
    ("/projects/projects.html", "weekly", "0.8"),
    ("/buying/guide_freehold_vs_leasehold_malaysia.html", "monthly", "0.7"),
    ("/buying/guide_subsale_property_malaysia.html", "monthly", "0.7"),
    ("/rental/guide_rental_deposit_malaysia.html", "monthly", "0.7"),
    ("/lelong/guide_lelong_property_malaysia.html", "monthly", "0.7"),
    ("/lelong/guide_lelong_reserve_vs_market_value.html", "monthly", "0.7"),
    ("/search.html", "monthly", "0.6"),
    ("/request.html", "monthly", "0.5"),
]


def _lastmod(rel_path: str) -> str:
    """YYYY-MM-DD the file was last committed (falls back to mtime, then today)."""
    import datetime
    import subprocess

    fs_path = ROOT / rel_path.lstrip("/")
    if rel_path == "/":
        fs_path = ROOT / "index.html"

    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(fs_path)],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
        )
        date = out.stdout.strip()
        if date:
            return date
    except Exception:
        pass

    try:
        ts = fs_path.stat().st_mtime
        return datetime.date.fromtimestamp(ts).isoformat()
    except OSError:
        return datetime.date.today().isoformat()


def regenerate_sitemap(area_files) -> None:
    """Rebuild sitemap.xml from CORE_PAGES + every file currently in area/local/.

    This runs every time the script runs, so any area page added or removed
    from area/local/ is automatically reflected -- no more manual sitemap
    edits, no more drift between the folder and what crawlers are told about.
    Each <url> gets a <lastmod> from the file's on-disk modified date so
    crawlers get a real freshness signal instead of none at all.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "",
        "  <!-- Core pages -->",
    ]
    for path, changefreq, priority in CORE_PAGES:
        lines += [
            "  <url>",
            f"    <loc>{SITE_BASE}{path}</loc>",
            f"    <lastmod>{_lastmod(path)}</lastmod>",
            f"    <changefreq>{changefreq}</changefreq>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ]

    lines += ["", "  <!-- Area pages (auto-generated from area/local/) -->"]
    for f in sorted(area_files, key=lambda p: p.name):
        rel = f"/area/local/{f.name}"
        lines += [
            "  <url>",
            f"    <loc>{SITE_BASE}{rel}</loc>",
            f"    <lastmod>{_lastmod(rel)}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.7</priority>",
            "  </url>",
        ]

    lines += ["", "</urlset>", ""]
    SITEMAP_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nsitemap.xml regenerated: {len(CORE_PAGES)} core pages + {len(area_files)} area pages")


def main():
    if not LISTINGS_CSV.exists():
        print(f"ERROR: {LISTINGS_CSV} not found", file=sys.stderr)
        sys.exit(1)
    rows = load_listings()
    print(f"Loaded {len(rows)} rows from listings.csv\n")

    area_files = sorted(AREA_DIR.glob("*.html"))
    print(f"Processing {len(area_files)} area pages...")
    for f in area_files:
        process_area_file(f, rows)

    regenerate_sitemap(area_files)

    print("\nProcessing kawasan.html area directory...")
    process_kawasan_page()
    sync_homepage_area_count()

    print("\nDone. Static SSR cards injected -- JS filtering/fetch still works as before.")


if __name__ == "__main__":
    main()
