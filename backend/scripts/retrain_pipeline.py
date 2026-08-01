"""
retrain_pipeline.py
Automated retrain pipeline: re-fetches real data, rebuilds the merged
dataset, and retrains the crop-loss model — one command instead of
manually running each script in sequence.

Usage: python backend/scripts/retrain_pipeline.py
"""
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_step(description, command, cwd=None):
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print('='*60)
    result = subprocess.run(command, shell=True, cwd=cwd or BASE_DIR)
    if result.returncode != 0:
        print(f"FAILED at step: {description}")
        sys.exit(1)
    print(f"Done: {description}")


def retrain_crop_loss():
    run_step(
        "Fetch IMD rainfall + temperature data",
        "python scripts/fetch_imd_data.py"
    )
    run_step(
        "Fetch NDVI data (AppEEARS)",
        "python scripts/fetch_ndvi_data.py"
    )
    run_step(
        "Fetch soil moisture data (NASA POWER API)",
        "python scripts/fetch_smap_data.py"
    )
    run_step(
        "Merge all data sources into training dataset",
        "python scripts/merge_crop_loss_data.py"
    )
    run_step(
        "Retrain crop-loss model (logs new version to registry)",
        "python -m modules.crop_loss"
    )
    print("\n" + "="*60)
    print("RETRAIN PIPELINE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    retrain_crop_loss()