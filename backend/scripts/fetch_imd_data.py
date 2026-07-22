"""
Fetches IMD gridded daily rainfall data (0.25x0.25 degree) via imdlib
and saves it as NetCDF for later merging with NDVI + SMAP data.
"""
import imdlib as imd
import os

# Where raw downloaded files land
OUTPUT_DIR = "data/raw/imd_rainfall"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Start small — test with 2 recent years first before pulling full history
START_YEAR = 2024
END_YEAR = 2024

def fetch_rainfall():
    data = imd.get_data(
        "rain",
        START_YEAR,
        END_YEAR,
        fn_format="yearwise",
        file_dir=OUTPUT_DIR,
    )
    print(f"Downloaded rainfall data for {START_YEAR}-{END_YEAR}")
    print(data)

def fetch_temperature():
    tmax = imd.get_data(
        "tmax",
        START_YEAR,
        END_YEAR,
        fn_format="yearwise",
        file_dir=OUTPUT_DIR.replace("imd_rainfall", "imd_temperature"),
    )
    tmin = imd.get_data(
        "tmin",
        START_YEAR,
        END_YEAR,
        fn_format="yearwise",
        file_dir=OUTPUT_DIR.replace("imd_rainfall", "imd_temperature"),
    )
    print(f"Downloaded tmax/tmin for {START_YEAR}-{END_YEAR}")


if __name__ == "__main__":
    fetch_rainfall()
    fetch_temperature()