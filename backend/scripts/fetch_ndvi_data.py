"""
fetch_ndvi_data.py
Fetches MODIS NDVI via NASA AppEEARS point-sample API — returns CSV directly,
no HDF4/GDAL/rasterio needed at all.

Setup (one-time):
1. pip install requests pandas
2. Use same NASA Earthdata account (urs.earthdata.nasa.gov) — free.
"""

import requests
import pandas as pd
import time
import os

APPEEARS_BASE = "https://appeears.earthdatacloud.nasa.gov/api"

# --- CONFIG ---
USERNAME = "yeshita2701"          # your Earthdata username
PASSWORD = os.environ.get("EARTHDATA_PASSWORD") or input("Earthdata password: ")

DISTRICT_NAME = "Pune"
LAT, LON = 18.52, 73.85            # Pune coordinates
START_DATE = "01-01-2024"
END_DATE = "12-31-2024"
OUTPUT_DIR = "backend/data/raw/modis_ndvi"


def get_token():
    resp = requests.post(f"{APPEEARS_BASE}/login", auth=(USERNAME, PASSWORD))
    resp.raise_for_status()
    return resp.json()["token"]


def submit_task(token):
    """Submits a point-sample task for MOD13Q1 NDVI at given lat/lon."""
    headers = {"Authorization": f"Bearer {token}"}
    task = {
        "task_type": "point",
        "task_name": f"ndvi_{DISTRICT_NAME}",
        "params": {
            "dates": [{"startDate": START_DATE, "endDate": END_DATE}],
            "layers": [{"product": "MOD13Q1.061", "layer": "_250m_16_days_NDVI"}],
            "coordinates": [{"latitude": LAT, "longitude": LON, "id": DISTRICT_NAME}],
        },
    }
    resp = requests.post(f"{APPEEARS_BASE}/task", json=task, headers=headers)
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    print(f"Task submitted: {task_id}")
    return task_id


def wait_for_completion(token, task_id):
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        resp = requests.get(f"{APPEEARS_BASE}/task/{task_id}", headers=headers)
        resp.raise_for_status()
        status = resp.json()["status"]
        print(f"Status: {status}")
        if status == "done":
            break
        elif status in ("error", "failed"):
            raise RuntimeError(f"Task failed: {resp.json()}")
        time.sleep(20)


def download_csv(token, task_id, output_dir):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{APPEEARS_BASE}/bundle/{task_id}", headers=headers)
    resp.raise_for_status()
    files = resp.json()["files"]

    csv_file = next((f for f in files if f["file_name"].endswith(".csv")), None)
    if not csv_file:
        raise RuntimeError("No CSV file found in task bundle.")

    file_id = csv_file["file_id"]
    file_resp = requests.get(
        f"{APPEEARS_BASE}/bundle/{task_id}/{file_id}", headers=headers, stream=True
    )
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"ndvi_{DISTRICT_NAME}.csv")
    with open(out_path, "wb") as f:
        for chunk in file_resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    print(f"--- NDVI fetch (AppEEARS): {DISTRICT_NAME}, {START_DATE} to {END_DATE} ---")
    token = get_token()
    task_id = submit_task(token)
    wait_for_completion(token, task_id)
    csv_path = download_csv(token, task_id, OUTPUT_DIR)

    df = pd.read_csv(csv_path)
    print(df.head())
    ndvi_col = [c for c in df.columns if "NDVI" in c]
    if ndvi_col:
        print("NDVI column found:", ndvi_col[0])
        print("Value range:", df[ndvi_col[0]].min(), df[ndvi_col[0]].max())