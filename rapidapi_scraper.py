#!/usr/bin/env python3
import sys
import os
import csv
import requests
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# ——— Load RapidAPI credentials ———
load_dotenv()  # expects RAPIDAPI_KEY & RAPIDAPI_HOST in .env
API_KEY  = os.getenv("RAPIDAPI_KEY")
API_HOST = os.getenv("RAPIDAPI_HOST")
if not API_KEY or not API_HOST:
    sys.exit("Missing RAPIDAPI_KEY or RAPIDAPI_HOST in .env")

# ——— Endpoint ———
BASE_URL = f"https://{API_HOST}/property_list/"

# ——— Parse cities from arguments ———
if len(sys.argv) < 2:
    sys.exit("Usage: python rapidapi_scraper.py \"City, ST\" [\"Other City, ST\" ...]")
CITIES = []
for arg in sys.argv[1:]:
    parts = [p.strip() for p in arg.split(",")]
    if len(parts) != 2:
        sys.exit(f"Invalid city format: {arg!r}. Use 'City, State'.")
    CITIES.append((parts[0], parts[1]))

# ——— Ensure output folder exists ———
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def process_city(city: str, state: str):
    """Fetch listings for a given city/state and write to CSV."""
    payload = {
        "query": {
            "status": ["for_sale"],
            "city": city,
            "state_code": state,
        },
        "limit": 50,
        "offset": 0,
        "sort": {"direction": "desc", "field": "list_date"}
    }
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST,
        "Content-Type": "application/json",
    }

    print(f"Fetching listings for {city}, {state}...")
    resp = requests.post(BASE_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # Extract the properties array
    listings = (
        data.get("data", {})
            .get("home_search", {})
            .get("properties", [])
    )
    if not listings:
        print("No properties found for", city, state)
        return    # ─── NEW EXTRACTION & DEBUG ───

    props = data.get("data", {})\
                .get("home_search", {})\
                .get("properties", [])
    if not props:
        print("No properties array found in response.") 
        return

    listings = props

    today = date.today().strftime("%Y%m%d")
    filename = f"listings_{city.replace(' ', '_')}_{state}_{today}.csv"
    output_path = DATA_DIR / filename

    # Write the CSV with the fields we want
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["address","price","beds","baths","sqft","list_date","detail_url"])
        for l in listings:
            address = l.get("location", {}).get("address", {}).get("line", "")
            price   = l.get("list_price", "")
            beds    = None
            baths   = None
            sqft    = None
            list_dt = l.get("list_date", "")
            detail  = l.get("permalink", "")
            writer.writerow([address, price, beds, baths, sqft, list_dt, detail])
    print(f"Saved {len(listings)} listings to {output_path}")

def main():
    for city, state in CITIES:
        try:
            process_city(city, state)
        except Exception as e:
            print(f"Error fetching {city}, {state}: {e}")

if __name__ == "__main__":
    main()

