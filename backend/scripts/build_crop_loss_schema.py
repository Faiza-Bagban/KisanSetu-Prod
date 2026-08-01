"""
build_crop_loss_schema.py
Drafts the unified schema/dataframe structure that IMD rainfall (Faiza),
NDVI (Yeshita), and SMAP soil moisture (Faiza, Day 4 onward) will merge into.

This does NOT do real data fetching — it defines the target columns and
generates a small dummy dataframe so everyone can agree on structure
before real data lands. Matches existing model features in
backend/modules/crop_loss.py: rainfall_deficit, temp_anomaly, ndvi_drop,
soil_moisture, days_since_rain.
"""

import pandas as pd
from datetime import date, timedelta
import random

# --- Unified schema definition ---
COLUMNS = [
    "district",          # str — e.g. "Pune"
    "date",              # date — observation date (weekly or 16-day cadence, TBD with team)
    "rainfall_deficit",  # float — mm below normal (from IMD, Faiza)
    "temp_anomaly",       # float — deg C above/below normal (from IMD, Faiza)
    "ndvi_drop",         # float — NDVI value drop vs seasonal baseline (from MODIS, Yeshita)
    "soil_moisture",     # float — SMAP volumetric soil moisture (from NASA SMAP, Faiza)
    "days_since_rain",   # int — consecutive dry days (from IMD, Faiza)
]


def generate_dummy_dataset(n_rows=10, district="Pune"):
    """Generates placeholder rows matching the schema — for structure review only."""
    rows = []
    start = date(2025, 6, 1)
    for i in range(n_rows):
        rows.append({
            "district": district,
            "date": start + timedelta(days=i * 16),  # matches MODIS 16-day cadence
            "rainfall_deficit": round(random.uniform(-20, 80), 2),
            "temp_anomaly": round(random.uniform(-2, 4), 2),
            "ndvi_drop": round(random.uniform(0, 0.3), 3),
            "soil_moisture": round(random.uniform(0.1, 0.4), 3),
            "days_since_rain": random.randint(0, 20),
        })
    return pd.DataFrame(rows, columns=COLUMNS)


if __name__ == "__main__":
    df = generate_dummy_dataset()
    print(df)
    output_path = "backend/data/processed/crop_loss_merged_DRAFT.csv"
    df.to_csv(output_path, index=False)
    print(f"\nDraft schema saved to {output_path} — share with Faiza to confirm column match.")