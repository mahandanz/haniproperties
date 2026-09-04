#!/usr/bin/env python3
"""
build_static_listings.py

Reads listings.csv and injects pre-rendered ("SSR") listing cards into each
area/local/*.html page, so the raw HTML contains real listing content
(project name, price, zone, etc.) instead of just "Loading listings...".

This is progressive enhancement, not a replacement:
- Your existing client-side JS (fetch + applyFilters) still runs exactly as
  before and takes over once loaded, giving live filtering/search.
- Search engines and AI crawlers that don't execute JS now see real content
  on first load instead of an empty placeholder.

Safe to re-run any time listings.csv changes — it replaces only the content
between the SSR markers, it does not duplicate on repeat runs.

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
            'onclick="cardImgNav(event,this,-1)" aria-label="Previous photo">\u2039</button>'
            '<button type="button" class="card-img-nav next" '
            'onclick="cardImgNav(event,this,1)" aria-label="Next photo">\u203a</button>'
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
        rf'(<div class="listing-grid" id="{grid_id}"><div class="loading">Loading listings\u2026</div>)(</div>)'
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

    print("\nDone. Static SSR cards injected -- JS filtering/fetch still works as before.")


if __name__ == "__main__":
    main()
