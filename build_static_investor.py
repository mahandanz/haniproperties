#!/usr/bin/env python3
"""
build_static_investor.py

Reads investor-listings.csv and injects pre-rendered ("SSR") unit cards into
investor-corner.html, so the raw HTML contains real content (project name,
price, cashflow, equity, etc.) instead of an empty grid.

This is progressive enhancement, not a replacement:
- The existing client-side JS (fetch + applyFilters) still runs exactly as
  before and takes over once loaded, giving live filtering.
- Search engines and AI crawlers that don't execute JS now see real content
  on first load instead of nothing.

Mirrors build_static_listings.py's approach for the area pages. Safe to
re-run any time investor-listings.csv changes -- it replaces only the
content between the SSR markers, it does not duplicate on repeat runs.

Usage:
    python3 build_static_investor.py
"""

import csv
import html
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
LISTINGS_CSV = ROOT / "investor-listings.csv"
PAGE_PATH = ROOT / "investor-corner.html"
WA_BASE = "https://wa.me/60125459182?text="

SSR_START = "<!--SSR_START-->"
SSR_END = "<!--SSR_END-->"

# Maps the friendly column headers used in the exported sheet to the
# internal field names this script works with. MUST stay in sync with
# the COLMAP object in investor-corner.html's client-side JS -- if you
# add/rename a column in one, add/rename it in the other too.
COLMAP = {
    "project": "Project",
    "area": "Area",
    "zone": "Zone",
    "type": "Type",
    "bed": "Bed",
    "bath": "Bath",
    "size": "Size (sqft)",
    "tenure": "Tenure",
    "price": "Price (RM)",
    "installment": "Installment (RM/mo)",
    "rental_fully": "Rental Fully",
    "cf_fully": "CF Fully",
    "yield_fully": "Yield% Fully",
    "equity_10yr": "Equity 10yr (RM)",
    "cum_cf_unfurnished_10yr": "Cumulative CF Unfurnished 10yr (RM)",
    "cum_cf_partial_10yr": "Cumulative CF Partial 10yr (RM)",
    "cum_cf_fully_10yr": "Cumulative CF Fully 10yr (RM)",
    "selling_cost_10yr": "Selling Cost 10yr (RM)",
    "equity_gain_net_10yr": "Equity Gain 10yr Net of Selling Cost (RM)",
    "cf_rating": "CF Rating (Best Case)",
    "date_added": "Date Added",
    "code": "Code",
}


def map_row(raw: dict) -> dict:
    """Translate a raw CSV row (friendly headers) into the snake_case
    field names the rest of this script expects."""
    return {key: raw.get(header) for key, header in COLMAP.items()}


def wa(text: str) -> str:
    return WA_BASE + urllib.parse.quote(text)


def esc(s) -> str:
    return html.escape(str(s or ""), quote=False)


def clean_count(v) -> str:
    """Bed/Bath sometimes arrive as '5.0' (source CSV stores them as a
    float-typed column). Show a clean integer when the value is whole,
    otherwise pass the original through unchanged."""
    if v is None or str(v).strip() == "":
        return ""
    n = to_num(v)
    if n is not None and n == int(n):
        return str(int(n))
    return str(v)


def to_num(v):
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return None


def fmt_price(v) -> str:
    n = to_num(v)
    if n is None:
        return "RM " + str(v)
    return "RM " + f"{int(n):,}"


def to_slug(*parts) -> str:
    joined = "-".join(str(p) for p in parts if p)
    slug = re.sub(r"[^a-z0-9]+", "-", joined.lower())
    return slug.strip("-")


def is_positive_cf(row: dict) -> bool:
    return "Strong" in (row.get("cf_rating") or "")


def deal_card(r: dict) -> str:
    project = r.get("project", "")
    area = r.get("area", "")
    zone = r.get("zone", "")
    price = to_num(r.get("price")) or 0
    rental_fully = to_num(r.get("rental_fully")) or 0
    cf_fully = to_num(r.get("cf_fully")) or 0
    yield_fully = to_num(r.get("yield_fully")) or 0
    equity_gain_net_10yr = to_num(r.get("equity_gain_net_10yr")) or 0
    cum_cf_fully_10yr = to_num(r.get("cum_cf_fully_10yr")) or 0
    nett_with_cf = equity_gain_net_10yr + cum_cf_fully_10yr
    bed = r.get("bed", "")
    bath = r.get("bath", "")
    size = to_num(r.get("size"))
    type_ = r.get("type", "")
    tenure = r.get("tenure", "")

    wa_text = (
        f"Hi Hani, I'm interested in {project}, {area} "
        f"(RM{int(price):,}) from the Investor Corner — can you share the full numbers on this one?"
    )

    bed_bath = ""
    if bed or bath:
        bed_bath = f'<span class="pill">\U0001F6CF {esc(clean_count(bed)) or "-"} bed \u00b7 \U0001F6BF {esc(clean_count(bath)) or "-"} bath</span>'
    size_pill = f'<span class="pill">{int(size):,} sqft</span>' if size else ""

    return f'''<div class="card" id="{to_slug(project, area, r.get('price'))}">
    <div class="card-body">
      <div><span class="card-badge badge-strong">\U0001F7E2 +{fmt_price(cf_fully)}/mo Cashflow</span></div>
      <div><div class="card-name">{esc(project)}</div><div class="card-zone">{esc(zone) + ', ' if zone else ''}{esc(area)}</div></div>
      <div class="card-price">{fmt_price(price)}</div>
      <div class="equity-block">
        <div class="equity-row"><span class="equity-label">\U0001F4C8 Nett Profit After 10 Yrs (with rental income)</span><span class="equity-amt">{fmt_price(nett_with_cf)}</span></div>
        <div class="equity-sub"><span>Without rental income</span><span>{fmt_price(equity_gain_net_10yr)}</span></div>
      </div>
      <div class="card-pills">{bed_bath}{size_pill}<span class="pill">{esc(type_)}</span><span class="pill">{esc(tenure)}</span></div>
      <a href="{wa(wa_text)}" class="card-cta" target="_blank" rel="noopener noreferrer">\U0001F4AC Ask Hani for the Full Numbers</a>
    </div>
  </div>'''


def empty_html(msg: str) -> str:
    return f'<div class="empty">{msg}</div>'


def load_listings():
    with open(LISTINGS_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [map_row(raw) for raw in reader]


def inject_grid(html_text: str, grid_id: str, cards_markup: str) -> str:
    """Replace content inside <div class="listing-grid" id="{grid_id}">...</div>
    with SSR-marked static cards. Works whether or not SSR markers already exist,
    and whether the grid is currently empty or not."""
    marker_pattern = re.compile(
        rf'(<div class="listing-grid" id="{grid_id}">){SSR_START}.*?{SSR_END}(</div>)',
        re.DOTALL,
    )
    empty_pattern = re.compile(
        rf'<div class="listing-grid" id="{grid_id}">\s*</div>'
    )

    replacement_full = f'<div class="listing-grid" id="{grid_id}">{SSR_START}{cards_markup}{SSR_END}</div>'

    if marker_pattern.search(html_text):
        return marker_pattern.sub(lambda m: replacement_full, html_text)
    if empty_pattern.search(html_text):
        return empty_pattern.sub(lambda m: replacement_full, html_text)
    print(f"    (warning: grid#{grid_id} not found in expected form, skipped)")
    return html_text


def inject_date_stamp(html_text: str, rows) -> str:
    """Fill in the 'Last updated' hero stamp statically too, so crawlers see
    a real date instead of the em-dash placeholder before JS runs."""
    dates = []
    for r in rows:
        d = (r.get("date_added") or "").strip()
        try:
            dates.append(datetime.strptime(d, "%d/%m/%Y"))
        except ValueError:
            continue
    if not dates:
        return html_text
    latest = max(dates).strftime("%-d %b %Y") if sys.platform != "win32" else max(dates).strftime("%#d %b %Y")
    return re.sub(
        r'(<span id="data-date">)[^<]*(</span>)',
        lambda m: f"{m.group(1)}{latest}{m.group(2)}",
        html_text,
        count=1,
    )


def main():
    if not LISTINGS_CSV.exists():
        print(f"ERROR: {LISTINGS_CSV} not found", file=sys.stderr)
        sys.exit(1)
    if not PAGE_PATH.exists():
        print(f"ERROR: {PAGE_PATH} not found", file=sys.stderr)
        sys.exit(1)

    rows = load_listings()
    print(f"Loaded {len(rows)} rows from investor-listings.csv")

    positive = [r for r in rows if is_positive_cf(r)]
    # Default order matches the page's JS: most extra money each month first
    positive.sort(key=lambda r: to_num(r.get("cf_fully")) or 0, reverse=True)

    cards_html = "".join(deal_card(r) for r in positive) if positive else empty_html(
        "No units match right now. Check back soon, or WhatsApp Hani directly."
    )

    text = PAGE_PATH.read_text(encoding="utf-8")
    text = inject_grid(text, "grid-deals", cards_html)
    text = inject_date_stamp(text, rows)
    PAGE_PATH.write_text(text, encoding="utf-8")

    print(f"investor-corner.html: {len(positive)} positive-cashflow units injected (of {len(rows)} total)")
    print("\nDone. Static SSR cards injected -- JS filtering/fetch still works as before.")


if __name__ == "__main__":
    main()
