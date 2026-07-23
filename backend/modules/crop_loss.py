import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# ── PATH SETUP ───────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE, "saved_models")
DATA_PATH = os.path.join(BASE, "data", "processed", "crop_loss_merged.csv")

os.makedirs(MODELS_DIR, exist_ok=True)

# ── LOAD REAL DATA ────────────────────────────────────────────
def load_real_data():
    """
    Loads the real merged dataset (IMD rainfall/temp, NDVI, soil moisture).
    No crop_type column — real data is district+date only, not crop-specific.
    No ground-truth 'risk' label exists yet (no real crop-loss/damage records
    collected) — applying the same heuristic threshold rule used previously,
    but now on REAL feature values instead of synthetic ones. This is a
    weak/heuristic label, not verified outcome data — replace with real
    PMFBY claim / disaster relief records when available.
    """
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    df["risk"] = (
        (df["rainfall_deficit"] > 30)
        | (df["ndvi_drop"] > 0.3)
        | (df["days_since_rain"] > 25)
    ).astype(int)

    return df

# ── TRAIN MODEL ──────────────────────────────────────────────
def train_model():
    df = load_real_data()

    le_district = LabelEncoder()
    df["district_enc"] = le_district.fit_transform(df["district"])

    features = [
        "district_enc",
        "rainfall_deficit",
        "temp_anomaly",
        "ndvi_drop",
        "soil_moisture",
        "days_since_rain"
    ]

    X = df[features]
    y = df["risk"]

    # Note: only 24 rows total — test split is small (5 rows). Accuracy
    # numbers here are indicative only, not statistically robust yet.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test) if len(X_test) else None

    print(f"Train accuracy: {train_acc:.2f}")
    if test_acc is not None:
        print(f"Test accuracy: {test_acc:.2f} (on {len(X_test)} rows — small sample, treat cautiously)")

    joblib.dump(model, os.path.join(MODELS_DIR, "crop_model.pkl"))
    joblib.dump(le_district, os.path.join(MODELS_DIR, "le_district.pkl"))

    print("Crop model saved at:", MODELS_DIR)

# ── PREDICT RISK ─────────────────────────────────────────────
def predict_risk(
    district: str,
    rainfall_deficit: float,
    temp_anomaly: float,
    ndvi_drop: float,
    soil_moisture: float,
    days_since_rain: int
) -> dict:

    try:
        model = joblib.load(os.path.join(MODELS_DIR, "crop_model.pkl"))
        le_district = joblib.load(os.path.join(MODELS_DIR, "le_district.pkl"))
    except FileNotFoundError:
        return {"error": "Model files not found. Run training first."}

    try:
        d_enc = le_district.transform([district])[0]
    except ValueError:
        return {"error": "Unknown district — model only trained on districts present in real data (currently: Pune)"}

    X = pd.DataFrame([{
        "district_enc": d_enc,
        "rainfall_deficit": rainfall_deficit,
        "temp_anomaly": temp_anomaly,
        "ndvi_drop": ndvi_drop,
        "soil_moisture": soil_moisture,
        "days_since_rain": days_since_rain,
    }])

    prob = model.predict_proba(X)[0][1]
    risk_pct = round(float(prob) * 100, 1)

    level = (
        "HIGH" if prob > 0.65
        else "MEDIUM" if prob > 0.35
        else "LOW"
    )

    result = {
        "district": district,
        "risk_level": level,
        "risk_percent": risk_pct,
        "alert": level == "HIGH",
    }

    if level == "HIGH":
        result["relief_draft"] = {
            "status": "PRE_FILLED",
            "action": "Initiate PMFBY claim process",
            "officer_note": f"{risk_pct}% loss probability detected",
        }

    return result

# ── LOCAL TEST ───────────────────────────────────────────────
if __name__ == "__main__":
    print("Training crop model on real data...")
    train_model()