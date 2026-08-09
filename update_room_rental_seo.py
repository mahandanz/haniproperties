#!/usr/bin/env python3
"""
update_room_rental_seo.py

Reads listings.csv and toggles the "room rental" SEO/AEO copy on each area page
on or off depending on whether that area currently has active room rental stock.

Usage:
    python3 update_room_rental_seo.py --csv listings.csv --area-dir area/local --out-dir area_updated

Rerun this anytime listings.csv changes (e.g. as part of your normal listing
update routine) to keep meta/schema copy in sync with actual inventory.
"""
import csv
import re
import argparse
import os
import sys
import shutil

# CSV area name -> area page filename slug (without .html)
AREA_SLUG_MAP = {
    "Ampang": "ampang",
    "Bandar Saujana Putra": "bandar-saujana-putra",
    "Bangi": "bangi",
    "Bukit Jalil": "bukit-jalil",
    "Cheras": "cheras",
    "Cyberjaya / Putrajaya": "cyberjaya-putrajaya",
    "Kajang": "kajang",
    "Kepong": "kepong",
    "Klang": "klang",
    "Kuala Lumpur": "kuala-lumpur",
    "Nilai": "nilai",
    "Petaling Jaya / Damansara": "petaling-jaya",
    "Puchong": "puchong",
    "Puncak Alam": "puncak-alam",
    "Rawang": "rawang",
    "Rimbayu/TPG": "rimbayu-tpg",
    "Selayang": "selayang",
    "Semenyih": "semenyih",
    "Sentul": "sentul",
    "Sepang": "sepang",
    "Seri Kembangan": "seri-kembangan",
    "Setapak": "setapak",
    "Shah Alam": "shah-alam",
    "Subang Jaya": "subang-jaya",
    "Sungai Buloh": "sungai-buloh",
}

ACTIVE_STATUSES = {"", "-"}  # blank / "-" = still available; rented/sold/booked = not counted

ROOM_ON_SUBS = [
    (re.compile(r'\brental and subsale\b'), 'rental, room rental and subsale'),
    (re.compile(r'\bRental and subsale\b'), 'Rental, room rental and subsale'),
    (re.compile(r'\bfor-rent and for-sale \(subsale\)\b'),
     'for-rent (including room rentals) and for-sale (subsale)'),
]
ROOM_OFF_SUBS = [
    (re.compile(r'\brental, room rental and subsale\b'), 'rental and subsale'),
    (re.compile(r'\bRental, room rental and subsale\b'), 'Rental and subsale'),
    (re.compile(r'\bfor-rent \(including room rentals\) and for-sale \(subsale\)\b'),
     'for-rent and for-sale (subsale)'),
]


def areas_with_active_rooms(csv_path):
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    active = set()
    for row in rows:
        if row.get("listing_type") == "room" and row.get("status", "") in ACTIVE_STATUSES:
            active.add(row.get("area", "").strip())
    return active


def apply_subs(content, subs):
    for pattern, repl in subs:
        content = pattern.sub(repl, content)
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--area-dir", required=True, help="folder containing the area .html files")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    active_areas = areas_with_active_rooms(args.csv)
    active_slugs = {AREA_SLUG_MAP[a] for a in active_areas if a in AREA_SLUG_MAP}

    report = []
    for fname in sorted(os.listdir(args.area_dir)):
        if not fname.endswith(".html"):
            continue
        slug = fname[:-5]
        src_path = os.path.join(args.area_dir, fname)
        with open(src_path, encoding="utf-8") as f:
            content = f.read()

        has_room = slug in active_slugs
        if has_room:
            content = apply_subs(content, ROOM_ON_SUBS)
        else:
            content = apply_subs(content, ROOM_OFF_SUBS)

        out_path = os.path.join(args.out_dir, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        report.append((slug, has_room))

    print(f"{'AREA':30s} ROOM RENTAL COPY")
    for slug, has_room in report:
        print(f"{slug:30s} {'ON' if has_room else 'off'}")

    unmapped = active_areas - set(AREA_SLUG_MAP.keys())
    if unmapped:
        print("\nNote: these CSV areas have active room listings but no matching area page:", unmapped)


if __name__ == "__main__":
    main()
