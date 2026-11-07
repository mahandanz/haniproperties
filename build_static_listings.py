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
    python3 build_static_listings.py              # normal run
    python3 build_static_listings.py --restamp    # also force every area page's
                                                  # "Last updated" date to today

Each area page's "Last updated" stamp (and its schema dateModified) is set to
today automatically whenever that page's listings change; a rebuild with the
same CSV leaves the date untouched.
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
        # Arrows + dots sit in a bar BELOW the photo (matches lightbox.js cardNavHTML)
        nav = (
            '<div class="card-img-bar">'
            '<button type="button" class="card-img-nav prev" '
            'onclick="cardImgNav(event,this,-1)" aria-label="Previous photo">‹</button>'
            f'<div class="card-img-dots">{dots}</div>'
            '<button type="button" class="card-img-nav next" '
            'onclick="cardImgNav(event,this,1)" aria-label="Next photo">›</button>'
            '</div>'
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
                    f'<strong style="color:#1B4D35;">RM {inst_val}</strong>/mo instalment</div>')
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


def _demand(r) -> float:
    """Demand % column as a number; blank/invalid sorts to the end."""
    try:
        return float(str(r.get("Demand %") or "").replace("%", "").strip())
    except ValueError:
        return -1.0


def _date_added(r) -> int:
    """date_added (D/M/YYYY) as YYYYMMDD; blank/invalid sorts to the end."""
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", (r.get("date_added") or "").strip())
    if not m:
        return 0
    return int(m.group(3)) * 10000 + int(m.group(2)) * 100 + int(m.group(1))


def sort_by_demand(rows):
    """Highest Demand % first; ties go to newest date_added. Matches the
    sortByDemand() function in the area pages' JS, so the static cards and
    the live cards appear in the same order."""
    return sorted(rows, key=lambda r: (_demand(r), _date_added(r)), reverse=True)


def empty_html(msg: str) -> str:
    return f'<div class="empty">{msg}</div>'


# ---------------------------------------------------------------------------
# Area summary
#
# Each area page's hero has a <p id="hero-summary-stat"> line. It used to be
# filled only by JavaScript, so the raw HTML Google first reads had it empty.
# The build now writes a factual, page-specific summary into it from
# listings.csv (counts, price ranges, main property types, a few building
# names). It updates itself on every rebuild, so it never goes stale.
# ---------------------------------------------------------------------------

# CSV "type" value (lowercase) -> plural wording used in the summary.
# Types not listed here fall back to "<type> units".
TYPE_PLURALS = {
    "condominium": "condos", "condo": "condos",
    "apartment": "apartments", "apartment (low cost)": "low-cost apartments",
    "service residence": "serviced residences", "serviced residence": "serviced residences",
    "service apartment": "serviced residences", "serviced apartment": "serviced residences",
    "terrace": "terrace homes", "townhouse": "townhouses", "cluster": "cluster homes",
    "semi d": "semi-Ds", "semi-d": "semi-Ds", "bungalow": "bungalows",
    "flat": "flats", "studio": "studios", "penthouse": "penthouses", "duplex": "duplexes",
    "soho": "SOHO units", "sofo": "SOFO units", "sovo": "SOVO units",
    "commercial": "commercial units", "shop lot": "shop lots", "shoplot": "shop lots",
    "office": "offices", "land": "land lots",
}


def _num_price(r):
    try:
        n = float(str(r.get("price") or "").replace(",", "").strip())
        return n if n > 0 else None
    except ValueError:
        return None  # ranges, TBC, blanks


def _join(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _price_range(rows, suffix=""):
    prices = sorted(p for p in (_num_price(r) for r in rows) if p)
    if not prices:
        return ""
    lo, hi = prices[0], prices[-1]
    if lo == hi:
        return f"at RM {int(lo):,}{suffix}"
    return f"from RM {int(lo):,} to RM {int(hi):,}{suffix}"


def _type_phrase(rows, with_beds=False):
    """'mostly 3-bedroom condos and apartments' / 'a mix of ...' / ''."""
    counts = {}
    for r in rows:
        t = (r.get("type") or "").strip()
        if not t or t == "-":
            continue
        plural = TYPE_PLURALS.get(t.lower(), f"{t} units")
        counts[plural] = counts.get(plural, 0) + 1
    typed = sum(counts.values())
    top = sorted(counts, key=lambda k: -counts[k])

    bed = ""
    if with_beds:
        beds = {}
        for r in rows:
            b = (r.get("bed") or "").strip()
            if b.isdigit() and int(b) > 0:
                beds[b] = beds.get(b, 0) + 1
        if beds:
            b, n = max(beds.items(), key=lambda kv: kv[1])
            if n / len(rows) >= 0.6:
                bed = f"{b}-bedroom"

    if not top:
        return f"mostly {bed} units" if bed else ""
    if len(top) == 1 or sum(counts[k] for k in top[:2]) / typed >= 0.6:
        lead = f"mostly {bed} " if bed else "mostly "
        return lead + _join(top[:2])
    phrase = "a mix of " + _join(top[:3])
    return phrase + (f", mostly {bed}" if bed else "")


# Commercial and land listings would skew a home price range (one shop lot at
# RM 6,500 a month next to RM 1,500 condos), so when a page mixes them in,
# the price range and type wording describe the homes only. Same wording as
# COMMERCIAL_RE in the area pages' JS.
NON_HOME_TYPE = re.compile(
    r"\b(commercial|shop ?lot|shop ?unit|shop ?office|shophouse|office|retail|factory"
    r"|warehouse|industrial|kedai|gudang|land|tanah)\b", re.I)


def _is_home(r) -> bool:
    return not NON_HOME_TYPE.search(r.get("type") or "")


def _segment(rows, verb, unit_word, suffix, with_beds):
    """e.g. '9 for rent from RM 1,300 to RM 2,500 a month, mostly ...'"""
    if not rows:
        return ""
    n = len(rows)
    head = f"{n} {unit_word if n == 1 else unit_word + 's'} {verb}" if unit_word else f"{n} {verb}"
    homes = [r for r in rows if _is_home(r)]
    if homes and len(homes) < n:
        # mixed page: describe the homes, so the range isn't skewed
        price = _price_range(homes, suffix)
        types = _type_phrase(homes, with_beds)
        out = head + (f", with homes {price}" if price else "")
        return out + (f", {types}" if types else "") + "."
    price = _price_range(rows, suffix)
    types = _type_phrase(rows, with_beds)
    out = head + (f" {price}" if price else "")
    return out + (f", {types}" if types else "") + "."


def area_summary(place: str, units, rooms, subsales) -> str:
    total = len(units) + len(rooms) + len(subsales)
    if not total:
        return (f"No listings in {place} at the moment. WhatsApp Hani to search "
                f"for units that aren't listed yet.")
    parts = [f"{total} active listing{'s' if total != 1 else ''} in {place}."]
    parts.append(_segment(units, "for rent", "", " a month", True))
    parts.append(_segment(rooms, "for rent", "room", " a month", False))
    parts.append(_segment(subsales, "for sale", "", "", False))

    # A few building names (highest demand first), the words people search for
    # ("Penduline (End Lot)" counts as Penduline; a name that's just the
    # area name, e.g. "Bandar Saujana Putra", is skipped)
    names, seen = [], {place.lower()}
    for r in units + rooms + subsales:
        nm = re.sub(r"\s*\([^)]*\)\s*$", "", " ".join((r.get("project_name") or "").split()))
        if nm and nm.lower() not in seen:
            seen.add(nm.lower())
            names.append(nm)
    if len(names) >= 2:
        parts.append(f"Listed buildings include {_join(names[:4])}.")
    return " ".join(p for p in parts if p)


SUMMARY_P = re.compile(r'(<p class="hero-desc" id="hero-summary-stat">).*?(</p>)', re.DOTALL)


def inject_summary(text: str, summary: str) -> str:
    if not SUMMARY_P.search(text):
        print("    (warning: #hero-summary-stat not found, summary skipped)")
        return text
    return SUMMARY_P.sub(lambda m: m.group(1) + esc(summary) + m.group(2), text, count=1)


# The page's own JS used to overwrite the summary line with a shorter
# "N current listings..." text once listings.csv loaded. This makes it only
# fill the line when the build hasn't already written one.
JS_SUMMARY_OLD = "if (summaryEl && totalListings) {"
JS_SUMMARY_NEW = "if (summaryEl && totalListings && !summaryEl.textContent.trim()) {"


def page_place_name(text: str, fallback: str) -> str:
    """Area name as shown in the page's <h1> ('Properties in X')."""
    m = re.search(r"<h1>Properties in ([^<]+)</h1>", text)
    return html.unescape(m.group(1)).strip() if m else fallback


def load_listings():
    with open(LISTINGS_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ---------------------------------------------------------------------------
# Instalment estimates
#
# Every subsale instalment is recomputed from its price with ONE formula,
# so cards never show figures worked out on different assumptions. These three
# numbers must match the disclaimer shown on the area pages ("Est. instalment
# based on 90% loan, 35-year tenure, 4.5% interest rate") -- change both
# together.
# ---------------------------------------------------------------------------
LOAN_MARGIN = 0.90      # 90% loan
LOAN_YEARS = 35         # 35-year tenure
LOAN_RATE = 4.5         # 4.5% p.a.
INSTALMENT_TYPES = ("subsale",)

# Land is financed differently from homes (lower margins, shorter tenures), so
# land listings show no instalment. Matches "Agricultural Land", "Land",
# "Tanah Pertanian" etc. in the type column -- but not "Landed" or "Landed Terrace".
LAND_TYPE = re.compile(r"\bland\b|\btanah\b", re.I)


def is_land(r) -> bool:
    return bool(LAND_TYPE.search(r.get("type") or ""))


def calc_instalment(price):
    """Monthly repayment (RM, rounded) on a standard reducing-balance loan."""
    try:
        p = float(str(price).replace(",", "").strip())
    except (ValueError, TypeError):
        return None  # price ranges like "300000-350000", "TBC", blanks
    if p <= 0:
        return None
    loan = p * LOAN_MARGIN
    r = LOAN_RATE / 100 / 12
    n = LOAN_YEARS * 12
    return round(loan * r / (1 - (1 + r) ** -n))


def normalise_instalments(rows) -> int:
    """Overwrite the installment column of every subsale row with the
    formula value. listings.csv is what the area pages' JavaScript and
    instalment filter read, so the CSV itself must hold the correct number --
    fixing only the static cards would be undone as soon as the JS loads.
    Returns how many rows changed."""
    changed = 0
    for r in rows:
        if r.get("listing_type") not in INSTALMENT_TYPES or "installment" not in r:
            continue
        if is_land(r):
            if (r.get("installment") or "").strip():
                print(f"    instalment: {r.get('project_name')} ({r.get('type')}) "
                      f"{r['installment']} -> removed (land)")
                r["installment"] = ""
                changed += 1
            continue
        val = calc_instalment(r.get("price"))
        if val is None:
            continue
        old = str(r.get("installment") or "").replace(",", "").strip()
        try:
            same = old and int(float(old)) == val
        except ValueError:
            same = False
        if not same:
            print(f"    instalment: {r.get('project_name')} (RM {r.get('price')}) "
                  f"{old or 'blank'} -> {val}")
            r["installment"] = str(val)
            changed += 1
    return changed


WA_PRICE = re.compile(r"(Price:\s*RM\s*)([\d,]+(?:\.\d+)?)", re.I)


def normalise_wa_prices(rows) -> int:
    """Keep the price inside each WhatsApp enquiry message (wa_text column,
    e.g. "... Price: RM310000. Ref: MMN") equal to the listing's price
    column, so the message a buyer sends always quotes the price on the card.
    Only rows with a plain numeric price are touched; ranges/TBC are skipped.
    Returns how many rows changed."""
    changed = 0
    for r in rows:
        text = r.get("wa_text") or ""
        if not text:
            continue
        price_raw = str(r.get("price") or "").replace(",", "").strip()
        try:
            price = int(float(price_raw))
        except ValueError:
            continue
        m = WA_PRICE.search(text)
        if not m:
            continue
        try:
            current = int(float(m.group(2).replace(",", "")))
        except ValueError:
            continue
        if current != price:
            r["wa_text"] = WA_PRICE.sub(lambda mm: f"{mm.group(1)}{price}", text, count=1)
            print(f"    whatsapp: {r.get('project_name')} Price: RM{current} -> RM{price}")
            changed += 1
    return changed


def save_listings(rows):
    """Write rows back to listings.csv, keeping its column order, BOM and
    line endings so the file stays as close to your original as possible."""
    raw = LISTINGS_CSV.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    with open(LISTINGS_CSV, encoding="utf-8-sig") as f:
        fieldnames = next(csv.reader(f))
    with open(LISTINGS_CSV, "w", encoding="utf-8-sig" if has_bom else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator=newline, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


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


def _strip_date_stamps(text: str) -> str:
    """Page text with the 'Last updated' / dateModified stamps blanked out,
    so a rebuild can tell whether the listings themselves actually changed."""
    text = re.sub(r"Last updated: [^<]*", "Last updated: ", text)
    return re.sub(r'"dateModified": "[^"]*"', '"dateModified": ""', text)


def stamp_dates(text: str, today) -> str:
    """Set the visible hero 'Last updated' stamp and the schema dateModified
    to today's date (e.g. 'Last updated: 1 Oct 2026' / "2026-10-01")."""
    text = re.sub(r"Last updated: [^<]*",
                  f"Last updated: {today.day} {today.strftime('%b %Y')}", text)
    return re.sub(r'"dateModified": "[^"]*"',
                  f'"dateModified": "{today.isoformat()}"', text)


# Area pages that were renamed or merged. Any link to an old file name inside
# an area page (e.g. a "Nearby Areas" link) is rewritten to the new page on
# every build. Add a line here whenever an area page is renamed or merged.
RENAMED_AREA_PAGES = {
    "sepang.html": "sepang-dengkil-banting.html",
    "sepang_dengkil_banting.html": "sepang-dengkil-banting.html",
    "kajang.html": "kajang-bangi.html",
    "bangi.html": "kajang-bangi.html",
    "nilai.html": "nilai-seremban.html",
}


def is_area_page(text: str) -> bool:
    """True if the page defines an AREA or AREAS constant (i.e. it's a real
    area listing page, not a stray file like area/local/search.html)."""
    return bool(re.search(r"const AREA\s*=\s*'", text) or re.search(r"const AREAS\s*=\s*\[", text))


def fix_area_urls(text: str, path: Path) -> str:
    """Keep each area page's own URLs correct and its links to other area
    pages pointing at the current file names:
      1. canonical and og:url always match this file's real name
      2. links to renamed/merged pages (RENAMED_AREA_PAGES) point to the new page
    """
    self_url = f"{SITE_BASE}/area/local/{path.name}"
    # Tolerant of attribute order, extra spaces and self-closing "/>".
    text = re.sub(r'(<link\b[^>]*\brel="canonical"[^>]*\bhref=")[^"]*(")',
                  rf'\g<1>{self_url}\g<2>', text)
    text = re.sub(r'(<link\b[^>]*\bhref=")[^"]*("[^>]*\brel="canonical")',
                  rf'\g<1>{self_url}\g<2>', text)
    text = re.sub(r'(<meta\b[^>]*\bproperty="og:url"[^>]*\bcontent=")[^"]*(")',
                  rf'\g<1>{self_url}\g<2>', text)
    text = re.sub(r'(<meta\b[^>]*\bcontent=")[^"]*("[^>]*\bproperty="og:url")',
                  rf'\g<1>{self_url}\g<2>', text)
    for old, new in RENAMED_AREA_PAGES.items():
        # matches href="sepang.html", href="/area/local/sepang.html",
        # href="https://haniproperties.com/area/local/sepang.html", meta
        # content="..." URLs, and the same URLs inside JSON-LD
        # ("item": "...sepang.html", "url": ..., "@id": ...)
        text = re.sub(rf'((?:href=|content=|"item":\s*|"url":\s*|"@id":\s*)"(?:[^"]*/)?){re.escape(old)}([#"])',
                      rf'\g<1>{new}\g<2>', text)
    return text


def process_area_file(path: Path, all_rows):
    text = path.read_text(encoding="utf-8")
    # A page may define a single AREA, a multi-value AREAS list, or both
    # (kajang-bangi.html only has AREAS, so it must not be skipped).
    m = re.search(r"const AREA\s*=\s*'([^']*)'", text)
    area = m.group(1) if m else None
    if not is_area_page(text):
        print(f"  skip {path.name}: no AREA or AREAS constant found")
        return

    # URL fixes are housekeeping, not a listings change, so they're applied
    # before the "did the listings change?" comparison below -- fixing a
    # canonical never moves the page's 'Last updated' date.
    text = fix_area_urls(text, path)
    # hreflang tags + EN | BM switch when a BM version exists (housekeeping)
    text = set_lang_links(text, path.stem, is_bm=False)
    # Template housekeeping (not a listings change): stop the page's JS from
    # overwriting the build-written summary line.
    text = text.replace(JS_SUMMARY_OLD, JS_SUMMARY_NEW)
    url_fixed = text != path.read_text(encoding="utf-8")
    original = text

    # Optional ZONE constant lets a page target a specific sub-area/township
    # within a broader CSV "area" value (e.g. Setia Alam is a "zone" inside
    # the "Shah Alam" area, not its own top-level area). When present, only
    # rows matching both area and zone are pulled into this page.
    zm = re.search(r"const ZONE\s*=\s*'([^']*)'", text)
    zone = zm.group(1) if zm else None

    # Optional AREAS constant lets one page cover several CSV "area" values
    # (e.g. sepang.html: const AREAS = ['Sepang', 'Dengkil', 'Banting'];).
    # Keeps the static SSR cards in sync with the page's client-side filter.
    # Falls back to the single AREA value when not present.
    am = re.search(r"const AREAS\s*=\s*\[([^\]]*)\]", text)
    areas = re.findall(r"'([^']*)'", am.group(1)) if am else []
    if not areas:
        if not area:
            print(f"  skip {path.name}: AREAS constant is empty")
            return
        areas = [area]

    filtered = [
        r for r in all_rows
        if r.get("area") in areas
        and (zone is None or r.get("zone") == zone)
        and (r.get("status") in ("-", "", None))
    ]
    units = sort_by_demand([r for r in filtered if r.get("listing_type") == "rental"])
    rooms = sort_by_demand([r for r in filtered if r.get("listing_type") == "room"])
    subsales = sort_by_demand([r for r in filtered if r.get("listing_type") == "subsale"])

    unit_html = "".join(unit_card(r) for r in units) if units else empty_html("No unit rentals available right now.")
    room_html = "".join(room_card(r) for r in rooms) if rooms else empty_html("No room rentals available right now.")
    subsale_html = "".join(subsale_card(r) for r in subsales) if subsales else empty_html("No subsale listings available right now.")

    text = inject_grid(text, "grid-unit", unit_html)
    text = inject_grid(text, "grid-room-tab", room_html)
    text = inject_grid(text, "grid-subsale", subsale_html)

    place = page_place_name(text, " / ".join(areas))
    text = inject_summary(text, area_summary(place, units, rooms, subsales))

    # Only move the 'Last updated' date when the listings on this page really
    # changed -- re-running the build with the same CSV leaves the date alone,
    # so the stamp stays an honest freshness signal for visitors and Google.
    if _strip_date_stamps(text) == _strip_date_stamps(original) and "--restamp" not in sys.argv:
        if url_fixed:
            path.write_text(text, encoding="utf-8")
        note = "URLs fixed, date kept" if url_fixed else "no change"
        print(f"  {path.name}: {' / '.join(areas)} -> {len(units)} rental, {len(rooms)} room, {len(subsales)} subsale ({note})")
        return units, rooms, subsales

    import datetime
    text = stamp_dates(text, datetime.date.today())
    path.write_text(text, encoding="utf-8")
    print(f"  {path.name}: {' / '.join(areas)} -> {len(units)} rental, {len(rooms)} room, {len(subsales)} subsale (updated, stamped {datetime.date.today().isoformat()})")
    return units, rooms, subsales


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
    {"slug": "setia-alam", "name": "Setia Alam", "region": "Selangor", "popular": True, "tag": "Setia City Mall, Setia Eco Park, NKVE"},
    {"slug": "petaling-jaya", "name": "Petaling Jaya / Damansara", "region": "Selangor", "popular": True, "tag": "1 Utama, IKEA Damansara, The Curve"},
    {"slug": "puchong", "name": "Puchong", "region": "Selangor", "popular": True, "tag": "IOI Mall, Setiawalk, PFCC"},
    {"slug": "subang-jaya", "name": "Subang Jaya", "region": "Selangor", "popular": True, "tag": "Sunway Pyramid, Empire, SS15"},
    {"slug": "klang", "name": "Klang", "region": "Selangor", "popular": True, "tag": "Bandar Botanic, AEON Bukit Tinggi"},
    {"slug": "kajang-bangi", "name": "Kajang & Bangi", "region": "Selangor", "tag": "MRT Kajang, UKM, IOI Mall Bangi"},
    {"slug": "semenyih", "name": "Semenyih", "region": "Selangor", "tag": "UNITEN, EcoHill Mall"},
    {"slug": "seri-kembangan", "name": "Seri Kembangan", "region": "Selangor", "tag": "The Mines, MRT Serdang Jaya"},
    {"slug": "cyberjaya-putrajaya", "name": "Cyberjaya / Putrajaya", "region": "Selangor", "popular": True, "tag": "MMU, IOI City Mall, KLIA Transit"},
    {"slug": "sepang", "page": "sepang-dengkil-banting", "name": "Sepang / Dengkil / Banting", "region": "Selangor", "tag": "KLIA, klia2, Sepang Circuit"},
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
    {"slug": "nilai", "page": "nilai-seremban", "name": "Nilai & Seremban", "region": "Negeri Sembilan", "tag": "USIM, AEON Nilai, Seremban 2, Senawang"},
]

REGION_ORDER = ["Selangor", "Kuala Lumpur", "Negeri Sembilan"]

# index.html's "Popular Areas We Cover" shows every area marked popular in
# AREAS above, in the same order. Mark/unmark "popular" there to change it.
HOME_AREAS = [a["slug"] for a in AREAS if a.get("popular")]


def area_card_html(a: dict) -> str:
    """Mirrors kawasan.html's client-side cardHtml() function exactly, so the
    SSR markup and the JS-rendered markup are visually identical."""
    popular = bool(a.get("popular"))
    popular_class = " popular" if popular else ""
    badge = '<span class="badge-popular">Popular</span>' if popular else ""
    name = html.escape(a["name"], quote=True)
    tag = html.escape(a["tag"], quote=False)
    slug = a["slug"]
    page = a.get("page") or slug  # page file name, if it differs from the image slug
    href = a.get("href") or f"area/local/{page}.html"  # BM directory passes its own link
    return (
        f'<a class="area-card{popular_class}" href="{href}">'
        f'<img class="area-card-img" src="/images/areas/{slug}.webp" alt="{name}" '
        f'loading="lazy" width="112" height="112" onerror="this.style.display=\'none\'">'
        f'<div class="area-card-body">'
        f'<div class="area-card-name">{name}{badge}</div>'
        f'<div class="area-card-tag">{tag}</div>'
        f'</div></a>'
    )


def render_area_directory_html(areas=None, bm=False) -> str:
    """Mirrors kawasan.html's client-side renderAreas() function: groups
    AREAS by region (in REGION_ORDER) and renders each region's label + grid."""
    areas = AREAS if areas is None else areas
    blocks = []
    for region in REGION_ORDER:
        items = [a for a in areas if a["region"] == region]
        if not items:
            continue
        count_label = (f'{len(items)} kawasan' if bm
                       else f'{len(items)} area{"s" if len(items) != 1 else ""}')
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


def js_areas_literal(areas=None) -> str:
    """Re-serialize AREAS as the `const AREAS = [...]` JS array literal, in
    the same shape kawasan.html's renderAreas()/cardHtml() already expect,
    so the inline <script> stays byte-for-byte in sync with the AREAS list
    above -- one source of truth, no hand-editing the JS array anymore."""
    lines = ["const AREAS = ["]
    for a in (AREAS if areas is None else areas):
        parts = [f"slug: '{_js_str(a['slug'])}'"]
        if a.get("page"):
            parts.append(f"page: '{_js_str(a['page'])}'")
        if a.get("href"):
            parts.append(f"href: '{_js_str(a['href'])}'")
        parts += [
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

    text = kawasan_lang_links(text, is_bm=False)
    KAWASAN_PATH.write_text(text, encoding="utf-8")
    print(f"  {KAWASAN_PATH.name}: {len(AREAS)} areas injected as static HTML across {len([r for r in REGION_ORDER if any(a['region'] == r for a in AREAS)])} regions")
    build_bm_kawasan(text)


def sync_homepage_areas():
    """Renders the HOME_AREAS cards into index.html's #home-areas grid, using
    the same area_card_html() as kawasan.html so the two pages always match."""
    if not HOMEPAGE_PATH.exists():
        return
    by_slug = {a["slug"]: a for a in AREAS}
    missing = [s for s in HOME_AREAS if s not in by_slug]
    if missing:
        print(f"    (warning: HOME_AREAS slugs not in AREAS: {', '.join(missing)})")
    # Homepage cards show at most 2 landmarks; kawasan.html keeps the full tag.
    cards = "".join(
        area_card_html({**by_slug[s], "tag": ", ".join(by_slug[s]["tag"].split(", ")[:2])})
        for s in HOME_AREAS if s in by_slug
    )
    text = HOMEPAGE_PATH.read_text(encoding="utf-8")
    pattern = re.compile(rf'<div class="area-grid" id="home-areas">{SSR_START}.*?{SSR_END}</div>', re.DOTALL)
    if not pattern.search(text):
        print("    (warning: #home-areas grid not found in index.html, skipped)")
        return
    new_text = pattern.sub(lambda m: f'<div class="area-grid" id="home-areas">{SSR_START}{cards}{SSR_END}</div>', text)
    if new_text != text:
        HOMEPAGE_PATH.write_text(new_text, encoding="utf-8")
    print(f"  {HOMEPAGE_PATH.name}: {len(HOME_AREAS)} homepage area cards rendered")


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
    ("/simple.html", "monthly", "0.8"),
    ("/calculator.html", "monthly", "0.8"),
    ("/projects/projects.html", "weekly", "0.8"),
    ("/buying/guide_freehold_vs_leasehold_malaysia.html", "monthly", "0.7"),
    ("/buying/guide_subsale_property_malaysia.html", "monthly", "0.7"),
    ("/rental/guide_rental_deposit_malaysia.html", "monthly", "0.7"),
    ("/commercial.html", "weekly", "0.8"),
    ("/land.html", "weekly", "0.8"),
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


def regenerate_sitemap(area_files, bm_files=()) -> None:
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

    # BM area pages (ms/area/*.html) -- built from bm_content.json
    if bm_files:
        lines += ["", "  <!-- BM area pages (auto-generated from bm_content.json) -->"]
    if bm_files and load_bm_kawasan():
        lines += [
            "  <url>",
            f"    <loc>{BM_KAWASAN_URL}</loc>",
            f"    <lastmod>{_lastmod('/ms/kawasan.html')}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.8</priority>",
            "  </url>",
        ]
    for f in sorted(bm_files, key=lambda p: p.name):
        rel = f"/ms/area/{f.name}"
        lines += [
            "  <url>",
            f"    <loc>{SITE_BASE}{rel}</loc>",
            f"    <lastmod>{_lastmod(rel)}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.7</priority>",
            "  </url>",
        ]

    # Area guides (guides/*.html) -- picked up automatically like area pages
    guide_files = sorted((ROOT / "guides").glob("*.html"))
    if guide_files:
        lines += ["", "  <!-- Area guides (auto-generated from guides/) -->"]
    for f in guide_files:
        rel = f"/guides/{f.name}"
        lines += [
            "  <url>",
            f"    <loc>{SITE_BASE}{rel}</loc>",
            f"    <lastmod>{_lastmod(rel)}</lastmod>",
            "    <changefreq>monthly</changefreq>",
            "    <priority>0.7</priority>",
            "  </url>",
        ]

    lines += ["", "</urlset>", ""]
    SITEMAP_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nsitemap.xml regenerated: {len(CORE_PAGES)} core pages + {len(area_files)} area pages + {len(bm_files)} BM area pages{' + BM kawasan' if bm_files and load_bm_kawasan() else ''} + {len(guide_files)} area guides")


# ---------------------------------------------------------------------------
# Bahasa Malaysia area pages (ms/area/*.html)
#
# Many people search in BM ("rumah sewa shah alam"), and Google prefers pages
# written in the searcher's language. For every area listed in bm_content.json
# the build writes a BM copy of the English area page to ms/area/<same name>,
# with:
#   - BM title, meta description, H1, intro, summary line and FAQ
#   - BM tabs, filters, buttons and card labels (listings data is unchanged)
#   - hreflang tags on BOTH pages, so Google treats them as language versions
#     of each other (not duplicates) and shows each searcher the right one
#   - an "EN | BM" switch at the top of both pages
# ms/area/ sits at the same folder depth as area/local/, so every relative
# link (../../index.html, ../../listings.csv, nearby areas) keeps working.
#
# To add an area: add its entry to bm_content.json and run the build.
# ---------------------------------------------------------------------------

BM_CONTENT_PATH = ROOT / "bm_content.json"
BM_DIR = ROOT / "ms" / "area"
BM_MONTHS = {"Jan": "Jan", "Feb": "Feb", "Mar": "Mac", "Apr": "Apr", "May": "Mei", "Jun": "Jun",
             "Jul": "Jul", "Aug": "Ogo", "Sep": "Sep", "Oct": "Okt", "Nov": "Nov", "Dec": "Dis"}
FURNISHING_BM = {"Fully Furnished": "Perabot Penuh", "Partially Furnished": "Separa Perabot",
                 "Unfurnished": "Tanpa Perabot"}

_BM_CACHE = None


def load_bm_content() -> dict:
    """{slug: entry} from bm_content.json (empty if the file is missing)."""
    global _BM_CACHE
    if _BM_CACHE is None:
        _BM_CACHE = {}
        if BM_CONTENT_PATH.exists():
            import json
            data = json.loads(BM_CONTENT_PATH.read_text(encoding="utf-8"))
            common = data.get("_common", {})
            for k, v in data.items():
                if not k.startswith("_"):
                    v = dict(v)
                    v["faq"] = list(v.get("faq", [])) + [
                        [q.replace("{place}", v["place"]), a.replace("{place}", v["place"])]
                        for q, a in common.get("faq", [])]
                    _BM_CACHE[k] = v
    return _BM_CACHE


def en_url(slug: str) -> str:
    return f"{SITE_BASE}/area/local/{slug}.html"


def bm_url(slug: str) -> str:
    return f"{SITE_BASE}/ms/area/{slug}.html"


HREFLANG_RE = re.compile(r"\s*<!--HREFLANG_START-->.*?<!--HREFLANG_END-->", re.S)
LANGSW_RE = re.compile(r"\s*<!--LANG_START-->.*?<!--LANG_END-->", re.S)
_SW_STYLE = ("margin:0 auto 12px;font-size:12px;font-weight:700;letter-spacing:.06em;"
             "color:rgba(255,255,255,.45)")
_SW_ON = "color:#fff"
_SW_LINK = "color:rgba(255,255,255,.7);text-decoration:underline;text-underline-offset:3px"


def set_lang_links(text: str, slug: str, is_bm: bool) -> str:
    """Add (or refresh) the hreflang tags and the EN | BM switch. On an English
    page they're only added when a BM version exists; otherwise removed."""
    text = HREFLANG_RE.sub("", text)
    text = LANGSW_RE.sub("", text)
    if slug not in load_bm_content():
        return text
    tags = (f'\n  <!--HREFLANG_START--><link rel="alternate" hreflang="en" href="{en_url(slug)}" />'
            f'<link rel="alternate" hreflang="ms" href="{bm_url(slug)}" />'
            f'<link rel="alternate" hreflang="x-default" href="{en_url(slug)}" /><!--HREFLANG_END-->')
    text = re.sub(r'(<link\b[^>]*\brel="canonical"[^>]*>)', lambda m: m.group(1) + tags, text, count=1)
    if is_bm:
        sw = (f'<a href="/area/local/{slug}.html" hreflang="en" lang="en" style="{_SW_LINK}">EN</a>'
              f' &nbsp;|&nbsp; <span style="{_SW_ON}" aria-current="page">BM</span>')
    else:
        sw = (f'<span style="{_SW_ON}" aria-current="page">EN</span> &nbsp;|&nbsp; '
              f'<a href="/ms/area/{slug}.html" hreflang="ms" lang="ms" style="{_SW_LINK}">BM</a>')
    block = f'\n  <!--LANG_START--><div class="lang-switch" style="{_SW_STYLE}">{sw}</div><!--LANG_END-->'
    return text.replace('<section class="hero">', '<section class="hero">' + block, 1)


# --- BM summary line (same facts as area_summary, in BM) --------------------

TYPE_BM = {
    "condominium": "kondominium", "condo": "kondominium",
    "apartment": "apartmen", "apartment (low cost)": "apartmen kos rendah",
    "service residence": "servis residensi", "serviced residence": "servis residensi",
    "service apartment": "servis residensi", "serviced apartment": "servis residensi",
    "terrace": "rumah teres", "townhouse": "townhouse", "cluster": "rumah kluster",
    "semi d": "semi-D", "semi-d": "semi-D", "bungalow": "banglo",
    "flat": "flat", "studio": "studio", "penthouse": "penthouse", "duplex": "dupleks",
    "soho": "unit SOHO", "sofo": "unit SOFO", "sovo": "unit SOVO",
    "commercial": "unit komersial", "shop lot": "lot kedai", "shoplot": "lot kedai",
    "office": "pejabat", "land": "tanah",
}


def _join_bm(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " dan " + items[-1]


def _price_range_bm(rows, suffix=""):
    prices = sorted(p for p in (_num_price(r) for r in rows) if p)
    if not prices:
        return ""
    lo, hi = prices[0], prices[-1]
    if lo == hi:
        return f"pada RM {int(lo):,}{suffix}"
    return f"dari RM {int(lo):,} hingga RM {int(hi):,}{suffix}"


def _type_phrase_bm(rows, with_beds=False):
    counts = {}
    for r in rows:
        t = (r.get("type") or "").strip()
        if not t or t == "-":
            continue
        word = TYPE_BM.get(t.lower(), t)
        counts[word] = counts.get(word, 0) + 1
    typed = sum(counts.values())
    top = sorted(counts, key=lambda k: -counts[k])
    bed = ""
    if with_beds:
        beds = {}
        for r in rows:
            b = (r.get("bed") or "").strip()
            if b.isdigit() and int(b) > 0:
                beds[b] = beds.get(b, 0) + 1
        if beds:
            b, n = max(beds.items(), key=lambda kv: kv[1])
            if n / len(rows) >= 0.6:
                bed = f"{b} bilik"
    if not top:
        return f"kebanyakannya unit {bed}" if bed else ""
    if len(top) == 1 or sum(counts[k] for k in top[:2]) / typed >= 0.6:
        return "kebanyakannya " + _join_bm(top[:2]) + (f" {bed}" if bed else "")
    return "gabungan " + _join_bm(top[:3]) + (f", kebanyakannya {bed}" if bed else "")


def _segment_bm(rows, verb, unit_word, suffix, with_beds):
    if not rows:
        return ""
    n = len(rows)
    head = f"{n} {unit_word} {verb}" if unit_word else f"{n} {verb}"
    homes = [r for r in rows if _is_home(r)]
    if homes and len(homes) < n:
        price = _price_range_bm(homes, suffix)
        types = _type_phrase_bm(homes, with_beds)
        out = head + (f", dengan rumah {price}" if price else "")
        return out + (f", {types}" if types else "") + "."
    price = _price_range_bm(rows, suffix)
    types = _type_phrase_bm(rows, with_beds)
    out = head + (f" {price}" if price else "")
    return out + (f", {types}" if types else "") + "."


def area_summary_bm(place, units, rooms, subsales) -> str:
    total = len(units) + len(rooms) + len(subsales)
    if not total:
        return (f"Tiada iklan di {place} buat masa ini. WhatsApp Hani untuk cari "
                f"unit yang belum disenaraikan.")
    parts = [f"{total} iklan aktif di {place}."]
    parts.append(_segment_bm(units, "untuk disewa", "", " sebulan", True))
    parts.append(_segment_bm(rooms, "untuk disewa", "bilik", " sebulan", False))
    parts.append(_segment_bm(subsales, "untuk dijual", "", "", False))
    names, seen = [], {place.lower()}
    for r in units + rooms + subsales:
        nm = re.sub(r"\s*\([^)]*\)\s*$", "", " ".join((r.get("project_name") or "").split()))
        if nm and nm.lower() not in seen:
            seen.add(nm.lower())
            names.append(nm)
    if len(names) >= 2:
        parts.append(f"Antara bangunan yang disenaraikan: {_join_bm(names[:4])}.")
    return " ".join(p for p in parts if p)


# --- Fixed UI wording: English -> BM ----------------------------------------
# Exact text swaps on the page (visible labels, filter options, card labels
# and the page's own JavaScript). Option values stay English so the filters
# still match listings.csv.
BM_UI = [
    # nav, hero, tabs
    ('>Home</a>', '>Utama</a>'),
    ('>Calculator</a>', '>Kalkulator</a>'),
    ("Can't Find It? Let Us Help", "Tak Jumpa? Kami Bantu Carikan"),
    ('>Browse units ↓</a>', '>Lihat unit ↓</a>'),
    ('✅ No registration needed — tap WhatsApp on any unit.', '✅ Tak perlu daftar — tekan WhatsApp pada mana-mana unit.'),
    ('>For Rent</button>', '>Sewa</button>'),
    ('>For Sale</button>', '>Jual</button>'),
    ('>Rooms</button>', '>Bilik</button>'),
    ('<div class="prop-choice-label">Property type</div>', '<div class="prop-choice-label">Jenis hartanah</div>'),
    ('<span>All</span>', '<span>Semua</span>'),
    ('<span>Residential</span>', '<span>Kediaman</span>'),
    ('<span>Commercial</span>', '<span>Komersial</span>'),
    ('<span>Land</span>', '<span>Tanah</span>'),
    # filters
    ('<div class="filter-label">Search</div>', '<div class="filter-label">Cari</div>'),
    ('placeholder="Project, seksyen, LRT, UiTM…"', 'placeholder="Projek, seksyen, LRT, UiTM…"'),
    ('aria-label="Search listings in this area"', 'aria-label="Cari iklan di kawasan ini"'),
    ('<div class="filter-label">Furnishing</div>', '<div class="filter-label">Perabot</div>'),
    ('<div class="filter-label">Type</div>', '<div class="filter-label">Jenis</div>'),
    ('<div class="filter-label">Bedrooms</div>', '<div class="filter-label">Bilik Tidur</div>'),
    ('<div class="filter-label">Room Type</div>', '<div class="filter-label">Jenis Bilik</div>'),
    ('<div class="filter-label">Max Price</div>', '<div class="filter-label">Harga Maksimum</div>'),
    ('<div class="filter-label">Max Instalment</div>', '<div class="filter-label">Ansuran Maksimum</div>'),
    ('<div class="filter-label">Tenure</div>', '<div class="filter-label">Pegangan</div>'),
    ('<option value="">All</option>', '<option value="">Semua</option>'),
    ('<option value="">Any</option>', '<option value="">Tiada had</option>'),
    ('<option>Fully Furnished</option>', '<option value="Fully Furnished">Perabot Penuh</option>'),
    ('<option>Partially Furnished</option>', '<option value="Partially Furnished">Separa Perabot</option>'),
    ('<option>Unfurnished</option>', '<option value="Unfurnished">Tanpa Perabot</option>'),
    ('<option>Freehold</option>', '<option value="Freehold">Pegangan Bebas (Freehold)</option>'),
    ('<option>Leasehold</option>', '<option value="Leasehold">Pajakan (Leasehold)</option>'),
    ('/mo</option>', '/bulan</option>'),
    ('/mo`', '/bulan`'),
    ('>Reset</button>', '>Set Semula</button>'),
    ('⚠️ Est. instalment based on 90% loan, 35-year tenure, 4.5% interest rate. Actual amount may vary depending on bank and eligibility.',
     '⚠️ Anggaran ansuran berdasarkan pinjaman 90%, tempoh 35 tahun dan kadar faedah 4.5%. Jumlah sebenar bergantung pada bank dan kelayakan anda.'),
    ('alt="Unit Rentals"', 'alt="Rumah sewa"'),
    ('alt="Room Rentals"', 'alt="Bilik sewa"'),
    ('alt="Subsales"', 'alt="Rumah dijual"'),
    # cards (static HTML and the JS that redraws them)
    ('>Unit Rental</span>', '>Sewa Unit</span>'),
    ('>Room Rental</span>', '>Sewa Bilik</span>'),
    ('<span> / month</span>', '<span> / bulan</span>'),
    ('💬 Enquire on WhatsApp', '💬 Tanya di WhatsApp'),
    ('\U0001F5D3 Move-in: ', '\U0001F5D3 Masuk: '),
    ('${r.bed} bed', '${r.bed} bilik'),
    ('${r.bath} bath', '${r.bath} bilik air'),
    ('">Est. <strong', '">Anggaran <strong'),
    ('</strong>/mo instalment</div>', '</strong>/bulan ansuran</div>'),
    ('${r.furnishing}</span>', '${FURNISHING_BM[r.furnishing] || r.furnishing}</span>'),
    ("Hi Hani, I'm interested in the subsale unit at ${r.project_name}",
     "Hai Hani, saya berminat dengan unit dijual di ${r.project_name}"),
    ("Hi Hani, I'm interested in a room at ${r.project_name}", "Hai Hani, saya berminat dengan bilik di ${r.project_name}"),
    ("Hi Hani, I'm interested in ${r.project_name}", "Hai Hani, saya berminat dengan ${r.project_name}"),
    # counts, empty states, errors
    ("${fu.length} listing${fu.length !== 1 ? 's' : ''}", "${fu.length} iklan"),
    ("${fs.length} listing${fs.length !== 1 ? 's' : ''}", "${fs.length} iklan"),
    ("${fr.length} listing${fr.length !== 1 ? 's' : ''}", "${fr.length} iklan"),
    ("'No unit rentals match your filters.'", "'Tiada rumah sewa yang sepadan dengan pilihan anda.'"),
    ("'No room rentals match your filters.'", "'Tiada bilik sewa yang sepadan dengan pilihan anda.'"),
    ("'No subsale listings match your filters.'", "'Tiada rumah dijual yang sepadan dengan pilihan anda.'"),
    ("No unit rentals available right now.", "Tiada rumah sewa buat masa ini."),
    ("No room rentals available right now.", "Tiada bilik sewa buat masa ini."),
    ("No subsale listings available right now.", "Tiada rumah dijual buat masa ini."),
    ('Nothing for "${escHtml(q)}" in ', 'Tiada hasil untuk "${escHtml(q)}" di '),
    ("'this area'", "'kawasan ini'"),
    ('Search all areas →', 'Cari semua kawasan →'),
    ('Tell us what you need', 'Beritahu kami apa yang anda cari'),
    ("'Unable to load listings. Please try again.'", "'Tidak dapat memuatkan iklan. Sila cuba lagi.'"),
    # bottom of page
    ("<h2>Don't see what you need?</h2>", "<h2>Tak jumpa yang anda cari?</h2>"),
    ('>Nearby Areas</span>', '>Kawasan Berdekatan</span>'),
    ('aria-label="Chat on WhatsApp"', 'aria-label="Sembang di WhatsApp"'),
    ('?text=Hi%20Hani%2C%20can%20you%20help%20me%3F"', '?text=Hai%20Hani%2C%20boleh%20bantu%20saya%3F"'),
]


def _json_ld_blocks(text):
    return list(re.finditer(r'(<script type="application/ld\+json">\s*)(.*?)(\s*</script>)', text, re.S))


def bm_page_text(en_text: str, slug: str, c: dict, summary: str) -> str:
    import json
    from urllib.parse import quote
    t = en_text
    place = c["place"]
    E = esc  # html-escape BM text going into the page

    # language + URLs
    t = t.replace('<html lang="en">', '<html lang="ms">', 1)
    t = t.replace('content="en_MY"', 'content="ms_MY"')
    t = re.sub(r'(<link\b[^>]*\brel="canonical"[^>]*\bhref=")[^"]*(")', rf'\g<1>{bm_url(slug)}\g<2>', t)
    t = re.sub(r'(<meta\b[^>]*\bproperty="og:url"[^>]*\bcontent=")[^"]*(")', rf'\g<1>{bm_url(slug)}\g<2>', t)

    # title + descriptions
    t = re.sub(r"<title>.*?</title>", lambda m: f"<title>{E(c['title'])}</title>", t, count=1, flags=re.S)
    for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
        t = re.sub(rf'(<meta {attr} content=")[^"]*(")', lambda m: m.group(1) + E(c["description"]) + m.group(2), t)
    for attr in ('property="og:title"', 'name="twitter:title"'):
        t = re.sub(rf'(<meta {attr} content=")[^"]*(")', lambda m: m.group(1) + E(c["title"]) + m.group(2), t)

    # structured data
    for m in reversed(_json_ld_blocks(t)):
        try:
            d = json.loads(m.group(2))
        except ValueError:
            continue
        if d.get("@type") == "FAQPage":
            d["inLanguage"] = "ms"
            d["mainEntity"] = [{"@type": "Question", "name": q,
                                "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in c["faq"]]
        elif "@graph" in d:
            for node in d["@graph"]:
                ty = node.get("@type")
                if ty == "CollectionPage":
                    node["@id"] = bm_url(slug) + "#page"
                    node["url"] = bm_url(slug)
                    node["name"] = c["h1"]
                    node["inLanguage"] = "ms"
                elif isinstance(ty, list) and "RealEstateAgent" in ty:
                    node["@id"] = bm_url(slug) + "#business"
                    node["url"] = bm_url(slug)
                    node["description"] = c["schema_description"]
                elif ty == "BreadcrumbList":
                    for it in node.get("itemListElement", []):
                        if it.get("name") in ("Areas", "Kawasan"):
                            it["name"] = "Kawasan"
                            if load_bm_kawasan():
                                it["item"] = BM_KAWASAN_URL
                        if it.get("item") == en_url(slug):
                            it["item"] = bm_url(slug)
        else:
            continue
        new = json.dumps(d, ensure_ascii=False)
        t = t[:m.start(2)] + new + t[m.end(2):]

    # hero
    t = re.sub(r"<h1>.*?</h1>", lambda m: f"<h1>{E(c['h1'])}</h1>", t, count=1, flags=re.S)
    t = re.sub(r'<p class="hero-desc">.*?</p>', lambda m: f'<p class="hero-desc">{E(c["intro"])}</p>',
               t, count=1, flags=re.S)
    t = SUMMARY_P.sub(lambda m: m.group(1) + E(summary) + m.group(2), t, count=1)

    def stamp(m):
        d, mon, y = m.group(1), m.group(2), m.group(3)
        return f"Dikemas kini setiap minggu · Kemas kini terakhir: {d} {BM_MONTHS.get(mon, mon)} {y}"
    t = re.sub(r"Updated weekly · Last updated: (\d+) ([A-Za-z]{3}) (\d{4})", stamp, t)
    t = re.sub(r"(📍 )(.*?) area overview →", r"\1Panduan kawasan \2 →", t)

    t = t.replace("&nbsp;·&nbsp; City Centre</div>", "&nbsp;·&nbsp; Pusat Bandar</div>")

    # breadcrumb label
    t = t.replace('kawasan.html">Areas</a>', 'kawasan.html">Kawasan</a>')
    if load_bm_kawasan():
        t = t.replace('href="../../kawasan.html">Kawasan</a>', 'href="../kawasan.html">Kawasan</a>')

    # CTA band
    t = re.sub(r"<p>Listings move fast\. WhatsApp Hani directly for the latest available units in .*?\.</p>",
               lambda m: f"<p>Unit cepat bertukar tangan. WhatsApp Hani terus untuk unit terkini di {E(place)}.</p>", t)
    msg = quote(f"Hai Hani, saya sedang mencari hartanah di {place}.")
    t = re.sub(r'(<div class="cta-band">.*?<a href="https://wa\.me/60125459182\?text=)[^"]*(")',
               lambda m: m.group(1) + msg + m.group(2), t, count=1, flags=re.S)

    # the JS fallback summary line (only shown if the build summary is empty)
    t = re.sub(r"`\$\{totalListings\} current listing\$\{totalListings !== 1 \? 's' : ''\} in (.*?) — for rent and for sale\.`",
               lambda m: f"`${{totalListings}} iklan semasa di {place} — untuk disewa dan dijual.`", t)

    # fixed UI wording
    for old, new in BM_UI:
        t = t.replace(old, new)
    for en, bm in FURNISHING_BM.items():
        t = t.replace(f'<span class="pill">{en}</span>', f'<span class="pill">{bm}</span>')
    t = re.sub(r"(🛏 [^<]*?) bed<", r"\1 bilik<", t)
    t = re.sub(r"(🚿 [^<]*?) bath<", r"\1 bilik air<", t)
    t = t.replace("const WA_BASE =",
                  "const FURNISHING_BM = " + json.dumps(FURNISHING_BM, ensure_ascii=False) + ";\nconst WA_BASE =", 1)

    # lightbox.js / search.js show BM labels on BM pages; new version tags so
    # browsers holding the older copy fetch the updated file
    t = re.sub(r"/lightbox\.js\?v=\w+", "/lightbox.js?v=20261104", t)
    t = t.replace('src="/search.js"', 'src="/search.js?v=20261103"')

    # links to other area pages: BM page if it exists, else the English one
    bm_slugs = set(load_bm_content())
    t = re.sub(r'href="([a-z0-9-]+)\.html"',
               lambda m: m.group(0) if m.group(1) in bm_slugs else f'href="../../area/local/{m.group(1)}.html"', t)

    # visible FAQ (same Q&A as the schema), just above the WhatsApp band
    items = "".join(
        f'<details style="border-bottom:1px solid #e3ddd0;padding:12px 0">'
        f'<summary style="cursor:pointer;font-weight:700;color:#1B4D35;font-size:15px">{E(q)}</summary>'
        f'<p style="margin:8px 0 0;color:#4a4540;font-size:14px;line-height:1.6">{E(a)}</p></details>'
        for q, a in c["faq"])
    faq = (f'<!--BM_FAQ_START--><section class="bm-faq" style="margin:32px 0 8px">'
           f'<h2 style="font-family:Lora,serif;color:#1B4D35;font-size:22px;margin:0 0 6px">'
           f'Soalan Lazim: Hartanah di {E(place)}</h2>{items}</section><!--BM_FAQ_END-->\n  ')
    t = t.replace('<div class="cta-band">', faq + '<div class="cta-band">', 1)

    return set_lang_links(t, slug, is_bm=True)


def build_bm_pages(area_results) -> list:
    """Write ms/area/<slug>.html for every area in bm_content.json.
    area_results: {slug: (units, rooms, subsales)} from the English build."""
    content = load_bm_content()
    if not content:
        return []
    BM_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    print(f"\nBuilding {len(content)} BM area pages (ms/area/)...")
    for slug, c in content.items():
        en_path = AREA_DIR / f"{slug}.html"
        if not en_path.exists() or slug not in area_results:
            print(f"  skip {slug}: no English page area/local/{slug}.html")
            continue
        units, rooms, subsales = area_results[slug]
        text = bm_page_text(en_path.read_text(encoding="utf-8"), slug, c,
                            area_summary_bm(c["place"], units, rooms, subsales))
        out = BM_DIR / f"{slug}.html"
        old = out.read_text(encoding="utf-8") if out.exists() else None
        if text != old:
            out.write_text(text, encoding="utf-8")
        print(f"  ms/area/{slug}.html: {'updated' if text != old else 'no change'}")
        written.append(out)
    # remove BM pages whose entry was taken out of bm_content.json
    for f in BM_DIR.glob("*.html"):
        if f.stem not in content:
            f.unlink()
            print(f"  removed ms/area/{f.name} (not in bm_content.json)")
    return written


# ---------------------------------------------------------------------------
# Bahasa Malaysia area directory (ms/kawasan.html)
#
# Built from the finished English kawasan.html, with the wording from the
# "_kawasan" entry in bm_content.json. Each card links to the area's BM page
# (or the English one if that area has no BM page yet). Both directories get
# hreflang tags and an EN | BM switch, like the area pages.
# ---------------------------------------------------------------------------

BM_KAWASAN_PATH = ROOT / "ms" / "kawasan.html"
BM_KAWASAN_URL = f"{SITE_BASE}/ms/kawasan.html"
EN_KAWASAN_URL = f"{SITE_BASE}/kawasan.html"


def load_bm_kawasan() -> dict:
    """The "_kawasan" entry of bm_content.json (empty if missing)."""
    if not BM_CONTENT_PATH.exists():
        return {}
    import json
    return json.loads(BM_CONTENT_PATH.read_text(encoding="utf-8")).get("_kawasan") or {}


def kawasan_lang_links(text: str, is_bm: bool) -> str:
    text = HREFLANG_RE.sub("", text)
    text = LANGSW_RE.sub("", text)
    if not load_bm_kawasan():
        return text
    tags = (f'\n<!--HREFLANG_START--><link rel="alternate" hreflang="en" href="{EN_KAWASAN_URL}" />'
            f'<link rel="alternate" hreflang="ms" href="{BM_KAWASAN_URL}" />'
            f'<link rel="alternate" hreflang="x-default" href="{EN_KAWASAN_URL}" /><!--HREFLANG_END-->')
    text = re.sub(r'(<link\b[^>]*\brel="canonical"[^>]*>)', lambda m: m.group(1) + tags, text, count=1)
    if is_bm:
        sw = (f'<a href="/kawasan.html" hreflang="en" lang="en" style="{_SW_LINK}">EN</a>'
              f' &nbsp;|&nbsp; <span style="{_SW_ON}" aria-current="page">BM</span>')
    else:
        sw = (f'<span style="{_SW_ON}" aria-current="page">EN</span> &nbsp;|&nbsp; '
              f'<a href="/ms/kawasan.html" hreflang="ms" lang="ms" style="{_SW_LINK}">BM</a>')
    block = f'\n    <!--LANG_START--><div class="lang-switch" style="{_SW_STYLE}">{sw}</div><!--LANG_END-->'
    return text.replace('<section class="area-hero">', '<section class="area-hero">' + block, 1)


def bm_kawasan_text(en_text: str, k: dict) -> str:
    import json
    E = esc
    t = en_text
    misses = []

    def sub(pattern, repl, flags=0):
        nonlocal t
        t, n = re.subn(pattern, repl, t, count=1, flags=flags)
        if not n:
            misses.append(pattern[:50])

    def swap(old, new):
        nonlocal t
        if old not in t:
            misses.append(old[:50])
        t = t.replace(old, new)

    # language, URLs, meta
    swap('<html lang="en">', '<html lang="ms">')
    swap('content="en_MY"', 'content="ms_MY"')
    sub(r'(<link\b[^>]*\brel="canonical"[^>]*\bhref=")[^"]*(")', rf'\g<1>{BM_KAWASAN_URL}\g<2>')
    sub(r'(<meta\b[^>]*\bproperty="og:url"[^>]*\bcontent=")[^"]*(")', rf'\g<1>{BM_KAWASAN_URL}\g<2>')
    sub(r"<title>.*?</title>", lambda m: f"<title>{E(k['title'])}</title>", re.S)
    sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + E(k["description"]) + m.group(2))
    sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + E(k["title"]) + m.group(2))
    sub(r'(<meta property="og:description" content=")[^"]*(")',
        lambda m: m.group(1) + E(k.get("og_description") or k["description"]) + m.group(2))

    # structured data
    for m in reversed(_json_ld_blocks(t)):
        try:
            d = json.loads(m.group(2))
        except ValueError:
            continue
        for node in d.get("@graph", []):
            if node.get("@type") == "CollectionPage":
                node["@id"] = BM_KAWASAN_URL + "#webpage"
                node["url"] = BM_KAWASAN_URL
                node["name"] = k["title"].split(" | ")[0]
                node["inLanguage"] = "ms"
            elif node.get("@type") == "BreadcrumbList":
                for it in node.get("itemListElement", []):
                    if it.get("item") == EN_KAWASAN_URL:
                        it["name"] = "Kawasan"
                        it["item"] = BM_KAWASAN_URL
        t = t[:m.start(2)] + json.dumps(d, ensure_ascii=False, indent=2) + t[m.end(2):]

    # nav (relative links in a page one folder down)
    swap('>Projects</a>', '>Projek</a>')
    swap('>Calculator</a>', '>Kalkulator</a>')

    # hero, breadcrumb, CTA
    sub(r'<div class="area-hero-eyebrow">.*?</div>', lambda m: f'<div class="area-hero-eyebrow">{E(k["eyebrow"])}</div>', re.S)
    sub(r'(<section class="area-hero">.*?)<h1>.*?</h1>', lambda m: m.group(1) + f'<h1>{E(k["h1"])}</h1>', re.S)
    sub(r'<p class="area-hero-desc">.*?</p>', lambda m: f'<p class="area-hero-desc">{E(k["intro"])}</p>', re.S)
    sub(r'(<span>›</span>\s*)Areas(\s*</div>)', r'\g<1>Kawasan\g<2>')
    sub(r"(<div class=\"cta-band\">\s*<h2>).*?(</h2>\s*<p>).*?(</p>\s*<a href=\")request\.html(\">).*?(</a>)",
        lambda m: (m.group(1) + E(k["cta_title"]) + m.group(2) + E(k["cta_text"]) + m.group(3)
                   + "/request.html" + m.group(4) + E(k["cta_button"]) + m.group(5)), re.S)

    # footer + floating WhatsApp button
    swap('Property in Selangor, KL &amp; Negeri Sembilan', 'Hartanah di Selangor, KL &amp; Negeri Sembilan')
    swap('aria-label="Chat on WhatsApp"', 'aria-label="Sembang di WhatsApp"')
    swap('?text=Hi%20Hani%2C%20can%20you%20help%20me%3F"', '?text=Hai%20Hani%2C%20boleh%20bantu%20saya%3F"')

    # area cards: BM landmarks + links to BM pages (static HTML and the JS copy)
    bm_slugs = set(load_bm_content())
    tags = k.get("tags", {})
    areas = []
    for a in AREAS:
        page = a.get("page") or a["slug"]
        href = f"/ms/area/{page}.html" if page in bm_slugs else f"/area/local/{page}.html"
        areas.append({**a, "tag": tags.get(a["slug"], a["tag"]), "href": href})
    t = inject_area_directory(t, render_area_directory_html(areas, bm=True))
    sub(r"const AREAS\s*=\s*\[.*?\];", lambda m: js_areas_literal(areas), re.S)
    swap('href="area/local/${a.page || a.slug}.html"', 'href="${a.href}"')
    swap("area${items.length > 1 ? 's' : ''}", "kawasan")

    if misses:
        print("    (warning: ms/kawasan.html -- not found in kawasan.html, left in English: "
              + "; ".join(misses) + ")")
    return kawasan_lang_links(t, is_bm=True)


def build_bm_kawasan(en_text: str):
    k = load_bm_kawasan()
    if not k:
        return
    text = bm_kawasan_text(en_text, k)
    BM_KAWASAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    old = BM_KAWASAN_PATH.read_text(encoding="utf-8") if BM_KAWASAN_PATH.exists() else None
    if text != old:
        BM_KAWASAN_PATH.write_text(text, encoding="utf-8")
    print(f"  ms/kawasan.html: {'updated' if text != old else 'no change'}")


# ---------------------------------------------------------------------------
# Commercial page (commercial.html) and Land page (land.html)
#
# Site-wide pages for every commercial and land listing, so these units are
# findable from the homepage (they are thin per area). Classified the same way
# as the Residential / Commercial / Land tabs on area pages and search.html
# (propClass() in their JS), so the counts always agree.
# ---------------------------------------------------------------------------
COMMERCIAL_PATH = ROOT / "commercial.html"
LAND_PATH = ROOT / "land.html"
COMMERCIAL_TYPE = re.compile(
    r"\b(commercial|shop ?lot|shop ?unit|shop ?office|shophouse|office|retail|"
    r"factory|warehouse|industrial|kedai|gudang)\b", re.I)
AGRI_TYPE = re.compile(r"agri|pertanian|kebun|orchard|farm", re.I)


def prop_class(r) -> str:
    c = (r.get("category") or "").strip().lower()
    if c in ("residential", "commercial", "land"):
        return c
    if is_land(r):
        return "land"
    if COMMERCIAL_TYPE.search(r.get("type") or ""):
        return "commercial"
    return "residential"


def _has(v) -> bool:
    s = str(v or "").strip()
    return bool(s) and s != "-"


def lc_card(r: dict) -> str:
    """Card for the Land & Commercial page. Same markup/classes as the area
    page cards (so lightbox.js popups work), minus bedroom pills and the
    instalment line, which don't apply to shops or land."""
    rent = r.get("listing_type") == "rental"
    cls = prop_class(r)
    if cls == "land":
        badge = '<span class="card-badge badge-land">Land · Sale</span>'
    elif rent:
        badge = '<span class="card-badge badge-unit">Commercial · Rent</span>'
    else:
        badge = '<span class="card-badge badge-subsale">Commercial · Sale</span>'
    size = size_pill(r)
    pills = "".join([
        f'<span class="pill pill-size">{size}</span>' if size else "",
        f'<span class="pill">{esc(r.get("type"))}</span>' if _has(r.get("type")) else "",
        f'<span class="pill">{esc(r.get("tenure"))}</span>' if (not rent and _has(r.get("tenure"))) else "",
        f'<span class="pill">{esc(r.get("furnishing"))}</span>' if (rent and _has(r.get("furnishing"))) else "",
        f'<span class="pill">{esc(r.get("parking/floor"))}</span>' if (rent and _has(r.get("parking/floor"))) else "",
        f'<span class="pill">{move_in_text(r.get("move_in_date"))}</span>' if (rent and move_in_text(r.get("move_in_date"))) else "",
    ])
    name = esc(r.get("project_name"))
    where = ", ".join(esc(x) for x in (r.get("zone"), r.get("area")) if _has(x))
    wa_text = r.get("wa_text") or f"Hi Hani, I'm interested in {r.get('project_name')}, {r.get('zone')}."
    anchors = f'<div class="card-anchors">{esc(r.get("anchors"))}</div>' if _has(r.get("anchors")) else ""
    per = "<span> / month</span>" if rent else ""
    return f'''<div class="card" id="{to_slug(r.get('project_name'), r.get('size'), r.get('price'))}">
    {card_image(r)}
    <div class="card-body">
      <div class="card-badges">{badge}{coa_badge(r.get('code'))}</div>
      <div><div class="card-name">{name}</div><div class="card-zone">{where}</div></div>
      <div class="card-price">{fmt_price(r.get('price'))}{per}</div>
      <div class="card-pills">{pills}</div>
      {anchors}
      <a href="{wa(wa_text)}" class="card-cta" target="_blank" rel="noopener noreferrer">\U0001F4AC Enquire on WhatsApp</a>
    </div>
  </div>'''


def _rng(rows, suffix=""):
    r = _price_range(rows, suffix)
    return " " + r if r else ""


def _n(rows, one, many):
    return f"{len(rows)} {one if len(rows) == 1 else many}"


def _areas(rows):
    n = len({r.get("area") for r in rows})
    return f"{n} area{'s' if n != 1 else ''}"


def _build_page(path: Path, grids, counts, summary, label) -> None:
    """Inject cards, jump-button counts and the summary line into a page,
    moving its 'Last updated' date only when the listings really changed."""
    if not path.exists():
        print(f"  {path.name} not found, skipped")
        return
    text = path.read_text(encoding="utf-8")
    original = text
    for gid, (rows, empty_msg) in grids.items():
        cards = "".join(lc_card(r) for r in rows) if rows else empty_html(empty_msg)
        text = inject_grid(text, gid, cards)
    for nid, n in counts.items():
        text = re.sub(rf'(<span class="n" id="n-{nid}">)[^<]*(</span>)', rf"\g<1>{n}\g<2>", text)
    text = re.sub(r'(<p class="hero-desc" id="hero-summary-stat">).*?(</p>)',
                  lambda m: m.group(1) + esc(summary) + m.group(2), text, flags=re.S)
    note = "no change"
    if _strip_date_stamps(text) != _strip_date_stamps(original) or "--restamp" in sys.argv:
        import datetime
        text = stamp_dates(text, datetime.date.today())
        note = "updated"
    if text != original:
        path.write_text(text, encoding="utf-8")
    print(f"  {path.name}: {label} ({note})")


def process_commercial_land_pages(all_rows) -> None:
    active = [r for r in all_rows if r.get("status") in ("-", "", None)]

    com = [r for r in active if prop_class(r) == "commercial"]
    rent = sort_by_demand([r for r in com if r.get("listing_type") == "rental"])
    sale = sort_by_demand([r for r in com if r.get("listing_type") == "subsale"])
    parts = []
    if rent:
        parts.append(_n(rent, "space for rent", "spaces for rent") + _rng(rent, " a month"))
    if sale:
        parts.append(_n(sale, "property for sale", "properties for sale") + _rng(sale))
    summary = (f"{len(rent) + len(sale)} commercial listings across {_areas(rent + sale)}: "
               + _join(parts) + ".") if parts else \
        "No commercial listings right now. WhatsApp Hani for off-market options."
    _build_page(COMMERCIAL_PATH,
                {"grid-commercial-rent": (rent, "No commercial space for rent right now."),
                 "grid-commercial-sale": (sale, "No commercial property for sale right now.")},
                {"commercial-rent": len(rent), "commercial-sale": len(sale)},
                summary, f"{len(rent)} rent, {len(sale)} sale")

    land = [r for r in active if prop_class(r) == "land"]
    agri = sort_by_demand([r for r in land if AGRI_TYPE.search(r.get("type") or "")])
    res = sort_by_demand([r for r in land if not AGRI_TYPE.search(r.get("type") or "")])
    parts = []
    if res:
        parts.append(_n(res, "residential or development lot", "residential or development lots") + _rng(res))
    if agri:
        parts.append(_n(agri, "agricultural lot", "agricultural lots") + _rng(agri))
    summary = (f"{len(land)} land listings for sale across {_areas(land)}: "
               + _join(parts) + ".") if parts else \
        "No land listings right now. WhatsApp Hani for off-market options."
    _build_page(LAND_PATH,
                {"grid-land-res": (res, "No residential land for sale right now."),
                 "grid-land-agri": (agri, "No agricultural land for sale right now.")},
                {"land-res": len(res), "land-agri": len(agri)},
                summary, f"{len(res)} residential, {len(agri)} agricultural")


def main():
    if not LISTINGS_CSV.exists():
        print(f"ERROR: {LISTINGS_CSV} not found", file=sys.stderr)
        sys.exit(1)
    rows = load_listings()
    print(f"Loaded {len(rows)} rows from listings.csv\n")

    print(f"Checking instalments ({int(LOAN_MARGIN*100)}% loan, {LOAN_YEARS} yrs, {LOAN_RATE}%)...")
    fixed = normalise_instalments(rows)
    print("Checking WhatsApp message prices match the price column...")
    wa_fixed = normalise_wa_prices(rows)
    if not wa_fixed:
        print("  all WhatsApp prices already match")
    fixed += wa_fixed
    if fixed:
        try:
            save_listings(rows)
            print(f"  {fixed} fix(es) saved to listings.csv\n")
        except PermissionError:
            print("\n  !! Could not save listings.csv -- it is open in another program "
                  "(usually Excel) or OneDrive is syncing it.")
            print("  !! Close it and run this script again. Nothing was changed in the CSV;")
            print("  !! the rest of this build continues with the corrected figures, but the")
            print("  !! live pages will show the old figures until the CSV itself is saved.\n")
    else:
        print("  listings.csv already correct, not changed\n")

    area_files = sorted(AREA_DIR.glob("*.html"))
    print(f"Processing {len(area_files)} area pages...")
    area_results = {}
    for f in area_files:
        res = process_area_file(f, rows)
        if res:
            area_results[f.stem] = res

    # Bahasa Malaysia copies of the area pages listed in bm_content.json
    bm_files = build_bm_pages(area_results)

    # Only real area pages go in the sitemap -- stray files in area/local/
    # (e.g. search.html) are left out.
    regenerate_sitemap([f for f in area_files if is_area_page(f.read_text(encoding="utf-8"))], bm_files)

    print("\nProcessing commercial.html and land.html...")
    process_commercial_land_pages(rows)

    print("\nProcessing kawasan.html area directory...")
    process_kawasan_page()
    sync_homepage_areas()
    sync_homepage_area_count()

    print("\nDone. Static SSR cards injected -- JS filtering/fetch still works as before.")


if __name__ == "__main__":
    main()
