"""
merge_crop_loss_data.py
Day 4 — Merges real NDVI data (from fetch_ndvi_data.py output) with
placeholder IMD rainfall + SMAP soil moisture data into the unified
crop-loss schema. Once Faiza's IMD/SMAP scripts are ready, swap the
placeholder loader functions with real ones — column names must match.

Final schema columns (must match backend/modules/crop_loss.py model input):
    district, date, rainfall_deficit, temp_anomaly, ndvi_drop,
    soil_moisture, days_since_rain
"""

import pandas as pd
import numpy as np
import os

NDVI_CSV_PATH = "backend/data/raw/modis_ndvi/ndvi_Pune.csv"
OUTPUT_PATH = "backend/data/processed/crop_loss_merged.csv"
NDVI_BASELINE = 0.45  # placeholder seasonal baseline NDVI for Pune — replace with real historical avg once available


def load_ndvi(path):
    """Loads real NDVI CSV from AppEEARS output, computes ndvi_drop vs baseline."""
    df = pd.read_csv(path)
    ndvi_col = [c for c in df.columns if "NDVI" in c][0]
    date_col = [c for c in df.columns if "Date" in c or "date" in c][0]

    out = pd.DataFrame({
        "district": df["ID"],
        "date": pd.to_datetime(df[date_col]),
        "ndvi_drop": (NDVI_BASELINE - df[ndvi_col]).clip(lower=0),  # only count drops, not rises
    })
    return out


def load_imd_rainfall_placeholder(dates, district="Pune"):
    """
    PLACEHOLDER — replace with Faiza's real IMD loader once ready.
    Must return columns: district, date, rainfall_deficit, temp_anomaly, days_since_rain
    """
    n = len(dates)
    return pd.DataFrame({
        "district": district,
        "date": dates,
        "rainfall_deficit": np.round(np.random.uniform(-10, 60, n), 2),
        "temp_anomaly": np.round(np.random.uniform(-1, 3, n), 2),
        "days_since_rain": np.random.randint(0, 15, n),
    })


def load_smap_placeholder(dates, district="Pune"):
    """
    PLACEHOLDER — replace with real SMAP soil moisture loader once ready.
    Must return columns: district, date, soil_moisture
    """
    n = len(dates)
    return pd.DataFrame({
        "district": district,
        "date": dates,
        "soil_moisture": np.round(np.random.uniform(0.15, 0.35, n), 3),
    })


def merge_all(ndvi_df, rainfall_df, smap_df):
    merged = ndvi_df.merge(rainfall_df, on=["district", "date"], how="left")
    merged = merged.merge(smap_df, on=["district", "date"], how="left")
    return merged[["district", "date", "rainfall_deficit", "temp_anomaly",
                    "ndvi_drop", "soil_moisture", "days_since_rain"]]


if __name__ == "__main__":
    ndvi_df = load_ndvi(NDVI_CSV_PATH)
    print(f"Loaded {len(ndvi_df)} NDVI rows for {ndvi_df['district'].iloc[0]}")

    rainfall_df = load_imd_rainfall_placeholder(ndvi_df["date"], ndvi_df["district"].iloc[0])
    smap_df = load_smap_placeholder(ndvi_df["date"], ndvi_df["district"].iloc[0])

    final_df = merge_all(ndvi_df, rainfall_df, smap_df)
    print(final_df)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved merged draft to {OUTPUT_PATH}")
    print("NOTE: rainfall/temp/soil_moisture columns are PLACEHOLDER data —")
    print("swap load_imd_rainfall_placeholder() and load_smap_placeholder() with")
    print("real functions once Faiza's IMD/SMAP scripts are ready.")