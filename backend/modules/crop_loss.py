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

os.makedirs(MODELS_DIR, exist_ok=True)

# ── SYNTHETIC TRAINING DATA ──────────────────────────────────
def generate_data(n=300):
    np.random.seed(42)

    districts = [
        "Nashik",
        "Pune",
        "Aurangabad",
        "Solapur",
        "Kolhapur",
        "Amravati"
    ]

    crops = [
        "wheat",
        "sugarcane",
        "onion",
        "soybean",
        "cotton",
        "rice"
    ]

    df = pd.DataFrame({
        "district": np.random.choice(districts, n),
        "crop_type": np.random.choice(crops, n),
        "rainfall_deficit": np.random.uniform(-50, 100, n),
        "temp_anomaly": np.random.uniform(-2, 5, n),
        "ndvi_drop": np.random.uniform(0, 0.5, n),
        "soil_moisture": np.random.uniform(10, 60, n),
        "days_since_rain": np.random.randint(0, 45, n),
    })

    df["risk"] = (
        (df["rainfall_deficit"] > 30)
        | (df["ndvi_drop"] > 0.3)
        | (df["days_since_rain"] > 25)
    ).astype(int)

    return df

# ── TRAIN MODEL ──────────────────────────────────────────────
def train_model():
    df = generate_data()

    le_district = LabelEncoder()
    le_crop = LabelEncoder()

    df["district_enc"] = le_district.fit_transform(df["district"])
    df["crop_enc"] = le_crop.fit_transform(df["crop_type"])

    features = [
        "district_enc",
        "crop_enc",
        "rainfall_deficit",
        "temp_anomaly",
        "ndvi_drop",
        "soil_moisture",
        "days_since_rain"
    ]

    X = df[features]
    y = df["risk"]

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

    # ── SAVE MODEL + ENCODERS ────────────────────────────────
    joblib.dump(
        model,
        os.path.join(MODELS_DIR, "crop_model.pkl")
    )

    joblib.dump(
        le_district,
        os.path.join(MODELS_DIR, "le_district.pkl")
    )

    joblib.dump(
        le_crop,
        os.path.join(MODELS_DIR, "le_crop.pkl")
    )

    print("✅ Crop model saved at:", MODELS_DIR)

# ── PREDICT RISK ─────────────────────────────────────────────
def predict_risk(
    district: str,
    crop_type: str,
    rainfall_deficit: float,
    temp_anomaly: float,
    ndvi_drop: float,
    soil_moisture: float,
    days_since_rain: int
) -> dict:

    # ── LOAD MODEL FILES ─────────────────────────────────────
    try:
        model = joblib.load(
            os.path.join(MODELS_DIR, "crop_model.pkl")
        )

        le_district = joblib.load(
            os.path.join(MODELS_DIR, "le_district.pkl")
        )

        le_crop = joblib.load(
            os.path.join(MODELS_DIR, "le_crop.pkl")
        )

    except FileNotFoundError:
        return {
            "error": "Model files not found. Run training first."
        }

    # ── ENCODE INPUTS ────────────────────────────────────────
    try:
        d_enc = le_district.transform([district])[0]
        c_enc = le_crop.transform([crop_type])[0]

    except ValueError:
        return {
            "error": "Unknown district or crop type"
        }

    # ── PREPARE INPUT DATA ───────────────────────────────────
    X = pd.DataFrame([{
        "district_enc": d_enc,
        "crop_enc": c_enc,
        "rainfall_deficit": rainfall_deficit,
        "temp_anomaly": temp_anomaly,
        "ndvi_drop": ndvi_drop,
        "soil_moisture": soil_moisture,
        "days_since_rain": days_since_rain,
    }])

    # ── PREDICT ──────────────────────────────────────────────
    prob = model.predict_proba(X)[0][1]

    risk_pct = round(float(prob) * 100, 1)

    level = (
        "HIGH"
        if prob > 0.65
        else "MEDIUM"
        if prob > 0.35
        else "LOW"
    )

    result = {
        "district": district,
        "crop_type": crop_type,
        "risk_level": level,
        "risk_percent": risk_pct,
        "alert": level == "HIGH",
    }

    # ── AUTO RELIEF DRAFT ────────────────────────────────────
    if level == "HIGH":
        result["relief_draft"] = {
            "status": "PRE_FILLED",
            "action": "Initiate PMFBY claim process",
            "officer_note": f"{risk_pct}% loss probability detected",
        }

    return result

# ── LOCAL TEST ───────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Training crop model...")
    train_model()