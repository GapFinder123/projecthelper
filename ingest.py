#!/usr/bin/env python3
"""
Usage:
    python ingest.py
This will:
  • read city_list.json
  • for each city, call rapidapi_scraper.py
  • find the generated CSV in data/
  • call csv_to_supabase.py on that CSV
"""
import subprocess, json
from pathlib import Path

# 1) load your cities
with open("city_list.json") as f:
    cities = json.load(f)

# 2) ensure data/ exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

for city in cities:
    print(f"\n--- Scraping {city!r} ---")
    subprocess.run(
        ["python", "rapidapi_scraper.py", city],
        check=True
    )

    # 3) find the most-recent CSV for that city
    #    name pattern: listings_<CityState>_YYYYMMDD.csv
    #    e.g. "Chelsea, AL" → "Chelsea_AL"
    cf = city.replace(", ", "_").replace(" ", "_")
    matches = sorted(data_dir.glob(f"listings_{cf}_*.csv"))
    if not matches:
        print(f"⚠️  No CSV found for {city!r}, skipping upload.")
        continue

    csv_file = matches[-1]
    print(f"Uploading {csv_file.name} to Supabase…")
    subprocess.run(
        ["python", "csv_to_supabase.py", str(csv_file)],
        check=True
    )

