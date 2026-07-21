# Updated Code

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os
from modules.crop_loss import predict_risk # adding test 6

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "eligibility_model.pkl")
CROP_ENCODER_PATH = os.path.join(BASE_DIR, "saved_models", "crop_encoder.pkl")
SCHEME_ENCODER_PATH = os.path.join(BASE_DIR, "saved_models", "scheme_encoder.pkl")

# adding task 3
DISTRICT_WEIGHTS = {
    "Nashik": {"DroughtRelief": 1.25, "PMFBY": 1.15, "NMSA": 1.10},
    "Solapur": {"DroughtRelief": 1.30, "PMFBY": 1.20},
    "Kolhapur": {"DroughtRelief": 0.85, "PMFBY": 0.95},
    "Pune": {"RKVY": 1.10, "PMKSY": 1.10}
}
# =========================
# Scheme Data
# =========================
# Adding Test 2 Seasons
SCHEMES = [
    {"id": "PM-KISAN",     "max_land": 5,   "max_income": 200000, "crops": "all","seasons": ["kharif", "rabi"], "documents": ["Aadhaar Card", "Land Ownership Proof", "Bank Passbook"],"description": "Provides direct income support of ₹6000 per year to small and marginal farmers."},
    {"id": "PMFBY",        "max_land": 10,  "max_income": 500000, "crops": "all", "seasons": ["kharif", "rabi"], "documents": ["Aadhaar Card", "Crop Details", "Bank Account"],"description": "Crop insurance scheme protecting farmers against yield loss due to natural calamities."},
    {"id": "SoilHealth",   "max_land": 10,  "max_income": 500000, "crops": "all","seasons": ["kharif", "rabi"], "documents": ["Soil Sample Report", "Farmer ID"],"description": "Provides soil health cards with nutrient analysis to improve crop productivity."},
    {"id": "KCC",          "max_land": 10,  "max_income": 300000, "crops": "all", "seasons": ["kharif", "rabi"], "documents": ["Aadhaar", "Land Records", "Bank Details"],"description": "Provides farmers with easy access to short-term credit for agricultural needs."},
    {"id": "NMSA",         "max_land": 3,   "max_income": 150000, "crops": "all","seasons": ["kharif"], "documents": ["Farmer ID", "Income Certificate"],"description": "Promotes sustainable agriculture through efficient water use and soil management."},
    {"id": "DroughtRelief","max_land": 5,   "max_income": 200000, "crops": "wheat,soybean,cotton","seasons": ["kharif"], "documents": ["Crop Loss Proof", "Weather Certificate"],"description": "Provides financial assistance to farmers affected by drought conditions."},
    {"id": "OrganicScheme","max_land": 4,   "max_income": 250000, "crops": "rice,wheat","seasons": ["rabi"], "documents": ["Organic Certification", "Farm Details"],"description": "Supports farmers in adopting organic farming practices with certification benefits."},
    {
    "id": "PMKSY",
    "max_land": 8,
    "max_income": 400000,
    "crops": "all",
    "seasons": ["kharif", "rabi"], 
    "documents": ["Aadhaar Card", "Land Records", "Irrigation Details"],
    "description": "Improves irrigation efficiency and ensures water access to every farm."
},
{
    "id": "RKVY",
    "max_land": 10,
    "max_income": 600000,
    "crops": "all",
    "seasons": ["kharif", "rabi"], 
    "documents": ["Project Proposal", "Farmer ID", "Bank Details"],
    "description": "Supports agricultural infrastructure and development projects at the state level."
},
{
    "id": "NFSM",
    "max_land": 6,
    "max_income": 300000,
    "crops": "rice,wheat,pulses",
    "seasons": ["rabi"], 
    "documents": ["Crop Details", "Land Records"],
    "description": "Aims to increase production of rice, wheat, and pulses for food security."
},
{
    "id": "PKVY",
    "max_land": 5,
    "max_income": 250000,
    "crops": "wheat,rice,cotton,soybean",
    "documents": ["Organic Certification", "Farmer ID"],
    "seasons": ["rabi"], 
    "description": "Promotes organic farming through cluster-based certification and support."
},
{
    "id": "eNAM",
    "max_land": 10,
    "max_income": 500000,
    "crops": "all",
    "seasons": ["kharif", "rabi"], 
    "documents": ["Aadhaar Card", "Bank Account", "Mobile Number"],
    "description": "Digital platform for farmers to sell produce across markets for better price discovery."
}
]

VALID_CROPS = ["wheat", "rice", "cotton", "soybean", "sugarcane"]
# MODEL_PATH = "eligibility_model.pkl"
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "eligibility_model.pkl") 

# =========================
# Encoders
# =========================
def get_encoders():
    # if os.path.exists("crop_encoder.pkl") and os.path.exists("scheme_encoder.pkl"):
    #     return joblib.load("crop_encoder.pkl"), joblib.load("scheme_encoder.pkl")
    if os.path.exists(CROP_ENCODER_PATH) and os.path.exists(SCHEME_ENCODER_PATH):
        return joblib.load(CROP_ENCODER_PATH), joblib.load(SCHEME_ENCODER_PATH)

    crop_le = LabelEncoder()
    crop_le.fit(["wheat", "rice", "cotton", "soybean", "sugarcane"])

    scheme_le = LabelEncoder()
    scheme_le.fit([s["id"] for s in SCHEMES])

    # joblib.dump(crop_le, "crop_encoder.pkl")
    # joblib.dump(scheme_le, "scheme_encoder.pkl")
    joblib.dump(crop_le, CROP_ENCODER_PATH)
    joblib.dump(scheme_le, SCHEME_ENCODER_PATH)

    return crop_le, scheme_le

# =========================
# Label Mapping
# =========================
def get_label(score):
    if score >= 80:
        return "Highly Eligible"
    elif score >= 60:
        return "Moderately Eligible"
    else:
        return "Low Eligibility"

# =========================
# Heuristic Scoring (Fallback)
# =========================
def calculate_score(land_size, income, crop_type, location, scheme):
    land_score = max(0, 1 - (land_size / scheme["max_land"]))
    income_score = max(0, 1 - (income / scheme["max_income"]))

    if scheme["crops"] == "all":
        crop_score = 1
    else:
        crop_score = 1 if crop_type in scheme["crops"].split(",") else 0

    location_score = 1

    final_score = (
        0.3 * land_score +
        0.4 * income_score +
        0.2 * crop_score +
        0.1 * location_score
    )

    return round(final_score * 100, 1)

# =========================
# Train Model
# =========================
def train_model():
    os.makedirs(os.path.join(BASE_DIR, "saved_models"), exist_ok=True)
    crop_le, scheme_le = get_encoders()

    data = []
    labels = []

    for s in SCHEMES:
        for _ in range(300):
            land = np.random.uniform(0.5, 10)
            income = np.random.uniform(50000, 500000)
            crop = np.random.choice(["wheat", "rice", "cotton", "soybean"])

            crop_encoded = crop_le.transform([crop])[0]
            scheme_encoded = scheme_le.transform([s["id"]])[0]

            eligible = 0
            if land <= s["max_land"] and income <= s["max_income"]:
                if s["crops"] == "all" or crop in s["crops"]:
                    eligible = 1

            data.append([land, income, crop_encoded, scheme_encoded])
            labels.append(eligible)

    model = RandomForestClassifier(n_estimators=100)
    model.fit(data, labels)

    joblib.dump(model, MODEL_PATH)
    print("✅ Final model trained!")

# =========================
# Load Model
# =========================
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

# =========================
# Match Schemes
# =========================
# Added Task 3
def apply_location_weighting(schemes, location):
    weights = DISTRICT_WEIGHTS.get(location, {})

    for s in schemes:
        mult = weights.get(s["scheme"], 1.0)
        score = s["confidence"] * mult

        # soft cap (avoid 99 clustering)
        if score > 95:
            score = 95 + (score - 95) * 0.5

        score = max(40, min(99, score))
        s["confidence"] = round(score, 1)

        if mult != 1.0:
            s["location_boost"] = f"{location} adjustment (x{mult})"

    return schemes
# Merging Task 4

def calibrate_confidence(schemes, land_size, income, crop_type):

    for s in schemes:
        
        score = s["confidence"]
        scheme = s["scheme"]

        # 🔥 Small farmer priority
        if land_size <= 1:
            if scheme == "PM-KISAN":
                score += 4
            elif scheme == "NMSA":
                score += 2

        # 💰 High income penalty
        if income > 300000:
            if scheme in ["PM-KISAN", "NMSA"]:
                score -= 10

        # 🌾 Crop relevance (light boost)
        if crop_type in ["wheat", "rice"]:
            if scheme in ["NFSM", "PKVY"]:
                score += 2

        # 🏗 Infrastructure schemes lower priority
        if scheme == "RKVY":
            score -= 8

        # 🎯 Ensure PM-KISAN is strong for small farmers
        if land_size <= 1 and scheme == "PM-KISAN":
            score = max(score, 96)

        # 🎯 Soft normalization (avoid clustering)
        if score > 95:
            score = 95 + (score - 95) * 0.3

        # Clamp
        score = max(40, score)

        s["confidence"] = round(score, 1)

    return schemes

# adding test 6
def apply_risk_boost(schemes, location, crop_type):
    # Basic location-based variation
    if location in ["Nashik", "Solapur"]:
        rainfall_deficit = 40
        ndvi_drop = 0.35
        days_since_rain = 25
    else:
        rainfall_deficit = 10
        ndvi_drop = 0.15
        days_since_rain = 8

    risk = predict_risk(
    district=location,
    crop_type=crop_type,
    rainfall_deficit=rainfall_deficit,
    temp_anomaly=2,
    ndvi_drop=ndvi_drop,
    soil_moisture=30,
    days_since_rain=days_since_rain
)
    # risk = predict_risk(
    #     district=location,
    #     crop_type=crop_type,
    #     rainfall_deficit=40,
    #     temp_anomaly=2,
    #     ndvi_drop=0.35,
    #     soil_moisture=25,
    #     days_since_rain=25
    # )

    risk_level = risk.get("risk_level", "LOW")

    for s in schemes:
        scheme_id = s["scheme"]

        if risk_level == "HIGH":
            if scheme_id == "PMFBY":
                s["confidence"] = min(99, s["confidence"] + 8)
                s["boost_reason"] = "High crop loss risk → Insurance prioritized"

            elif scheme_id == "DroughtRelief":
                s["confidence"] = min(95, s["confidence"] + 4)
                s["boost_reason"] = "Drought conditions likely"

            else:
                # mild penalty (deterministic, not random)
                s["confidence"] = max(40, s["confidence"] - 5)

        s["confidence"] = round(min(s["confidence"], 99), 1)
        s["explanation"] = f"Adjusted based on {risk_level} risk in {location}"

    return schemes

# adding test 5
def generate_recommendations(land_size, income, crop_type, location, matched):

    if not isinstance(matched, list):
        return matched

    matched_ids = [s["scheme"] for s in matched]

    recommendations = []

    for scheme in SCHEMES:

        if scheme["id"] in matched_ids:
            continue

        reasons = []
        priority = 0

        if land_size > scheme["max_land"]:
            gap = round(land_size - scheme["max_land"], 2)
            gap = int(gap) if gap.is_integer() else gap
            unit = "acre" if gap == 1 else "acres"
            reasons.append(f"reduce land by {gap} {unit} (max {scheme['max_land']} acres)")
            priority += 1

        if income > scheme["max_income"]:
            gap = int(income - scheme["max_income"])
            reasons.append(f"reduce declared income by ₹{gap:,} to qualify")
            priority += 1

        if scheme["crops"] != "all" and crop_type not in scheme["crops"]:
            reasons.append(f"switch to eligible crops ({scheme['crops']})")
            priority += 2

        if reasons:
            recommendation = f"For {scheme['id']}: " + ", ".join(reasons)
            recommendations.append((priority, recommendation))

    recommendations = sorted(recommendations, key=lambda x: x[0])
    recommendations = [r[1] for r in recommendations]
    if not recommendations:
        recommendations = ["You are eligible for all available schemes."]

    return recommendations

def match_schemes(land_size, income, crop_type, district, season=None): #adding test 2
    if crop_type not in VALID_CROPS:
        return {
            "schemes": [],
            "message": f"No schemes available for crop '{crop_type}'. Please enter a valid crop."
        }
    matched = []
    model = load_model()
    crop_le, scheme_le = get_encoders()

    for s in SCHEMES:
        if season:
            season = season.lower()
            if season and season not in s.get("seasons", []):
                continue
        if land_size <= s["max_land"] and income <= s["max_income"]:

            # =========================
            # ML Prediction
            # =========================
            if model:
                try:
                    crop_encoded = crop_le.transform([crop_type])[0]
                    scheme_encoded = scheme_le.transform([s["id"]])[0]

                    prob = model.predict_proba([
                        [land_size, income, crop_encoded, scheme_encoded]
                    ])[0][1]

                    score = float(prob) * 100
                except:
                    score = calculate_score(land_size, income, crop_type, district, s)
            else:
                score = calculate_score(land_size, income, crop_type, district, s)

            # =========================
            # 🔥 REALISM FIX (Penalty System)
            # =========================
            penalty = 0

            # stricter schemes → reduce score
            if s["max_land"] <= 3:
                penalty += 5
            if s["max_income"] <= 200000:
                penalty += 5

            # crop mismatch penalty
            # if s["crops"] != "all" and crop_type not in s["crops"]:
            if s["crops"] != "all" and crop_type not in s["crops"].split(","):
                penalty += 10

            score = max(0, round(score - penalty, 1))
            score = min(score, 98)  # added line - cap max confidence
            if score < 40:
                continue

            matched.append({
                "scheme": s["id"],
                "confidence": score,
                "eligibility": get_label(score),
                "documents_required": s.get("documents", []),
                "description": s.get("description", "No description available")  #added
            })

            #adding test 4
    matched = calibrate_confidence(matched, land_size, income, crop_type)
    # adding test 3
    matched = apply_location_weighting(matched, district)
    matched = apply_risk_boost(matched, district, crop_type) # adding test 6

    recommendations = generate_recommendations(land_size, income, crop_type, district, matched) #adding test 5

    
    matched = sorted(matched, key=lambda x: -x["confidence"])
    return {
        "schemes": matched,
        "recommendations": recommendations
    }

# =========================
# Main Test
# =========================
if __name__ == "__main__":
    # Train once
    if not os.path.exists(MODEL_PATH):
        train_model()

    result = match_schemes(1.5, 80000, "wheat", "Nashik")

    print("\n🎯 Eligible Schemes:\n")
    for r in result:
        print(r)