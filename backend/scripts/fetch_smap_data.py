"""
Fetches NASA SMAP soil moisture data via earthaccess (NASA's official client).
Downloads a small test range first before scaling to full district coverage.
"""

import earthaccess
import os
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = "data/raw/smap_soil_moisture"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_smap():
    auth = earthaccess.login(strategy="environment")
    print("Logged in:", auth.authenticated)

    results = earthaccess.search_data(
        short_name="SPL3SMP_E",
        temporal=("2024-06-01", "2024-09-30"),
        bounding_box=(72.5, 15.5, 80.5, 22.0),
    )
    print(f"Found {len(results)} granules")

    downloaded = []
    for i, granule in enumerate(results, 1):
        print(f"Downloading granule {i}/{len(results)}...")
        try:
            files = earthaccess.download([granule], OUTPUT_DIR, threads=1)
            downloaded.extend(files)
            print(f"  done: {files}")
        except Exception as e:
            print(f"  FAILED: {e}")

    print("\nAll downloads finished:", downloaded)

if __name__ == "__main__":
    fetch_smap()