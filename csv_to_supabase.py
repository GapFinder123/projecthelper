#!/usr/bin/env python3
"""
Usage:
    python csv_to_supabase.py data/listings_<City>_YYYYMMDD.csv [more.csv ...]
"""
import os
import sys
import csv
import datetime
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load Supabase credentials from .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    sys.exit("Missing SUPABASE_URL or SUPABASE_KEY in .env")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE_NAME = "listings"

def coerce(val, fn):
    try:
        return fn(val) if val not in ("", None) else None
    except Exception:
        return None

def row_from_csv(row: dict, path: Path) -> dict:
    # Derive city name from filename: listings_CityState_YYYYMMDD.csv
    stem = path.stem  # e.g. "listings_Chelsea_AL_20250626"
    city_state = stem.replace("listings_", "").rsplit("_", 1)[0]  # -> "Chelsea_AL"
    city = city_state.replace("_", " ")

    # Grab list_date directly (it's already a string like "2025-06-26")
    date_added = row.get("list_date") or None
    # Use today's date as an ISO string
    date_scraped = datetime.date.today().isoformat()

    return {
        "address":        row.get("address") or None,
        "city":           city,
        "beds":           coerce(row.get("beds"), int),
        "baths":          coerce(row.get("baths"), int),
        "price":          coerce(row.get("price"), float),
        "date_added":     date_added,
        "link":           row.get("detail_url"),
        "listing_source": "rapidapi_scraper",
        "date_scraped":   date_scraped,
    }

def upload_file(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [row_from_csv(r, path) for r in reader if r.get("detail_url")]
    if not rows:
        print(f"[{path.name}] No rows to upload.")
        return
    # ─── DEDUPE ROWS ON link ───
    seen = set()
    unique = []
    for r in rows:
        link = r.get("link")
        if link and link not in seen:
            unique.append(r)
            seen.add(link)
    if len(unique) < len(rows):
        print(f"[{path.name}] Removed {len(rows)-len(unique)} duplicate rows before upload.")
    rows = unique
    # ────────────────────────────

    try:
        res = supabase.table(TABLE_NAME).upsert(rows, on_conflict="link").execute()
        # success if no exception
        print(f"[{path.name}] Upserted {len(rows)} rows.")
    except Exception as e:
        # any HTTP error or JSON error will be caught here
        print(f"[{path.name}] ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python csv_to_supabase.py data/listings_<City>_YYYYMMDD.csv [more.csv ...]")
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.exists():
            upload_file(p)
        else:
            print(f"File not found: {p}")

