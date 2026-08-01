"""
merge_crop_loss_data.py
Merges real NDVI, IMD rainfall/temperature, and soil moisture (NASA POWER API)
data into the unified crop-loss schema.

Final schema columns (must match backend/modules/crop_loss.py model input):
    district, date, rainfall_deficit, temp_anomaly, ndvi_drop,
    soil_moisture, days_since_rain
"""

import pandas as pd
import numpy as np
import os
import imdlib as imd

NDVI_CSV_PATH = "backend/data/raw/modis_ndvi/ndvi_Pune.csv"
OUTPUT_PATH = "backend/data/processed/crop_loss_merged.csv"
NDVI_BASELINE = 0.45  # placeholder seasonal baseline NDVI for Pune — replace with real historical avg once available

PUNE_LAT, PUNE_LON = 18.52, 73.85


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


def load_imd_rainfall(dates, district="Pune"):
    """
    Real IMD loader — for each NDVI date, aggregates the preceding 16-day
    window of daily rainfall/temp into rainfall_deficit, temp_anomaly,
    and days_since_rain.
    """
   
    rain_data = imd.open_data("rain", 2024, 2024, fn_format="yearwise", file_dir="data/raw/imd_rainfall")
    rain_ds = rain_data.get_xarray().where(lambda d: d != -999.0)
    rain_series = rain_ds.sel(lat=PUNE_LAT, lon=PUNE_LON, method="nearest")["rain"]

    tmax_data = imd.open_data("tmax", 2024, 2024, fn_format="yearwise", file_dir="data/raw/imd_temperature")
    tmax_ds = tmax_data.get_xarray().where(lambda d: d != -999.0)
    tmax_series = tmax_ds.sel(lat=PUNE_LAT, lon=PUNE_LON, method="nearest")["tmax"]

    overall_mean_temp = float(tmax_series.mean())

    rows = []
    for d in dates:
        window_start = d - pd.Timedelta(days=16)
        window_rain = rain_series.sel(time=slice(window_start, d))
        window_tmax = tmax_series.sel(time=slice(window_start, d))

        total_rain = float(window_rain.sum())
        avg_temp = float(window_tmax.mean()) if len(window_tmax) else overall_mean_temp

        dry_days = 0
        for val in reversed(window_rain.values):
            if val is None or val == 0:
                dry_days += 1
            else:
                break

        rows.append({
            "district": district,
            "date": d,
            "rainfall_deficit": round(50 - total_rain, 2),
            "temp_anomaly": round(avg_temp - overall_mean_temp, 2),
            "days_since_rain": dry_days,
        })
    return pd.DataFrame(rows)


def load_smap(dates, district="Pune"):
    """Loads soil moisture from NASA POWER API CSV, averages over each 16-day window."""
    moisture_df = pd.read_csv("backend/data/raw/smap_soil_moisture/soil_moisture_pune.csv")
    moisture_df["date"] = pd.to_datetime(moisture_df["date"])

    rows = []
    for d in dates:
        window_start = d - pd.Timedelta(days=16)
        window = moisture_df[(moisture_df["date"] >= window_start) & (moisture_df["date"] <= d)]
        avg_moisture = round(float(window["soil_moisture"].mean()), 3) if len(window) else None
        rows.append({"district": district, "date": d, "soil_moisture": avg_moisture})
    return pd.DataFrame(rows)


def merge_all(ndvi_df, rainfall_df, smap_df):
    merged = ndvi_df.merge(rainfall_df, on=["district", "date"], how="left")
    merged = merged.merge(smap_df, on=["district", "date"], how="left")
    return merged[["district", "date", "rainfall_deficit", "temp_anomaly",
                    "ndvi_drop", "soil_moisture", "days_since_rain"]]


if __name__ == "__main__":
    ndvi_df = load_ndvi(NDVI_CSV_PATH)
    print(f"Loaded {len(ndvi_df)} NDVI rows for {ndvi_df['district'].iloc[0]}")

    rainfall_df = load_imd_rainfall(ndvi_df["date"], ndvi_df["district"].iloc[0])
    smap_df = load_smap(ndvi_df["date"], ndvi_df["district"].iloc[0])

    final_df = merge_all(ndvi_df, rainfall_df, smap_df)
    print(final_df)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved merged (REAL DATA) to {OUTPUT_PATH}")