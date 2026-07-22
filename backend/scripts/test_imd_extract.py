"""
Quick test: read downloaded IMD data and extract rainfall
for one district (Pune) on one sample date.
"""
import imdlib as imd

data = imd.open_data("rain", 2022, 2023, fn_format="yearwise", file_dir="data/raw/imd_rainfall")

ds = data.get_xarray()
print(ds)

# Pune coordinates: ~18.52 N, 73.85 E
pune_rain = ds.sel(lat=18.52, lon=73.85, method="nearest")
print("\nSample Pune rainfall (first 10 days):")
print(pune_rain["rain"].values[:10])