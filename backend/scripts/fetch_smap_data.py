"""
Fetches soil moisture via NASA POWER API (simpler REST alternative to SMAP satellite downloads).
Returns GWETROOT (root-zone soil wetness, 0-1 scale) for Pune, daily.
"""
import requests
import pandas as pd
import os

OUTPUT_DIR = "backend/data/raw/smap_soil_moisture"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LAT, LON = 18.52, 73.85
START_DATE = "20240101"
END_DATE = "20241231"

def fetch_soil_moisture():
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "GWETROOT",
        "community": "AG",
        "longitude": LON,
        "latitude": LAT,
        "start": START_DATE,
        "end": END_DATE,
        "format": "JSON",
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    values = data["properties"]["parameter"]["GWETROOT"]
    df = pd.DataFrame([
        {"date": pd.to_datetime(d, format="%Y%m%d"), "soil_moisture": v}
        for d, v in values.items()
    ])
    df.to_csv(f"{OUTPUT_DIR}/soil_moisture_pune.csv", index=False)
    print(f"Saved {len(df)} days of soil moisture data")
    print(df.head())

if __name__ == "__main__":
    fetch_soil_moisture()