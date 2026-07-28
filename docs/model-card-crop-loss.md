# Model Card: Crop-Loss Risk Prediction

## Overview
Predicts drought/crop-loss risk for a district based on rainfall deficit,
temperature anomaly, NDVI (vegetation health), soil moisture, and days
since last rain.

## Model
XGBoost classifier, 100 estimators, max depth 4.

## Training Data
- **Source**: Real IMD (India Meteorological Department) rainfall/temperature
  data, MODIS NDVI via NASA AppEEARS, soil moisture via NASA POWER API
- **Coverage**: Pune district, full year 2024, 24 data points (16-day NDVI
  composite intervals)
- **Known limitation**: Small sample size (24 rows) — cross-validation
  accuracy (0.76 ± 0.15) should be treated as indicative, not precise.
  More districts and years of data would meaningfully improve reliability.

## Label
**No real ground-truth crop-loss/damage records exist yet** (e.g. PMFBY
claims, disaster relief records). The "risk" label is a heuristic rule:
`rainfall_deficit > 30mm OR ndvi_drop > 0.3 OR days_since_rain > 25`.
This is a reasonable proxy but not verified against actual crop outcomes.
Replace with real damage-record data when available for a genuinely
supervised model.

## Known Limitations
- Trained only on Pune — will reject predictions for other districts
  until retrained with their data
- No crop-type specificity (real data doesn't include this dimension)
- Heuristic label, not verified ground truth (see above)

## Versioning
Tracked via `backend/modules/model_registry.py` — every retrain logs
version, timestamp, and metrics to `backend/saved_models/registry.json`.

## Retraining
Run `python backend/scripts/retrain_pipeline.py` to re-fetch all data
sources and retrain in one command.