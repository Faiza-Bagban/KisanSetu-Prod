import json, os, sys

# So it can find crop_loss module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.crop_loss import predict_risk

# 6 district scenarios with realistic stress data
SCENARIOS = [
    {"district": "Nashik",     "crop_type": "wheat",     "rainfall_deficit": 45, "temp_anomaly": 2.1, "ndvi_drop": 0.38, "soil_moisture": 22, "days_since_rain": 30},
    {"district": "Pune",       "crop_type": "sugarcane", "rainfall_deficit": 15, "temp_anomaly": 1.0, "ndvi_drop": 0.15, "soil_moisture": 40, "days_since_rain": 10},
    {"district": "Aurangabad", "crop_type": "cotton",    "rainfall_deficit": 60, "temp_anomaly": 3.5, "ndvi_drop": 0.42, "soil_moisture": 15, "days_since_rain": 35},
    {"district": "Solapur",    "crop_type": "soybean",   "rainfall_deficit": 55, "temp_anomaly": 3.0, "ndvi_drop": 0.40, "soil_moisture": 18, "days_since_rain": 28},
    {"district": "Kolhapur",   "crop_type": "rice",      "rainfall_deficit": 5,  "temp_anomaly": 0.5, "ndvi_drop": 0.08, "soil_moisture": 55, "days_since_rain": 4},
    {"district": "Amravati",   "crop_type": "soybean",   "rainfall_deficit": 50, "temp_anomaly": 2.8, "ndvi_drop": 0.35, "soil_moisture": 20, "days_since_rain": 26},
]

# District coordinates for Leaflet map
COORDINATES = {
    "Nashik":     {"lat": 19.9975, "lng": 73.7898},
    "Pune":       {"lat": 18.5204, "lng": 73.8567},
    "Aurangabad": {"lat": 19.8762, "lng": 75.3433},
    "Solapur":    {"lat": 17.6599, "lng": 75.9064},
    "Kolhapur":   {"lat": 16.7050, "lng": 74.2433},
    "Amravati":   {"lat": 20.9374, "lng": 77.7796},
}

def precompute():
    results = []

    for s in SCENARIOS:
        print(f"Computing {s['district']}...")
        r = predict_risk(**s)

        results.append({
            "district":     r["district"],
            "crop_type":    r["crop_type"],
            "risk_level":   r["risk_level"],      # HIGH / MEDIUM / LOW
            "risk_percent": r["risk_percent"],
            "alert":        r["alert"],
            "lat":          COORDINATES[r["district"]]["lat"],
            "lng":          COORDINATES[r["district"]]["lng"],
            "relief_draft": r.get("relief_draft", None),
        })

    # Save to backend/data/
    OUT_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
    OUT_FILE = os.path.join(OUT_DIR, "district_risks.json")
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(OUT_FILE, "w") as f:
        json.dump({"districts": results}, f, indent=2)

    print(f"\nSaved to backend/data/district_risks.json")
    print(f"Total districts: {len(results)}")
    print(f"HIGH risk:   {sum(1 for r in results if r['risk_level'] == 'HIGH')}")
    print(f"MEDIUM risk: {sum(1 for r in results if r['risk_level'] == 'MEDIUM')}")
    print(f"LOW risk:    {sum(1 for r in results if r['risk_level'] == 'LOW')}")

if __name__ == "__main__":
    precompute()