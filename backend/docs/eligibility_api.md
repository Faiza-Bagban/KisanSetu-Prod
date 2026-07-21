# 🌾 KisanSetu Eligibility API Documentation

## 📌 Overview

The Eligibility API recommends government schemes for farmers based on:

* Land size
* Income
* Crop type
* Location (district)
* Season (Kharif / Rabi)

It also:

* Adjusts results using **risk prediction**
* Applies **location-based weighting**
* Provides **actionable recommendations** to unlock more schemes

---

# 🚀 Base URL

```
http://localhost:8000
```

---

# 📡 Endpoint: Get Eligible Schemes

## 🔹 POST `/api/eligibility`

### 📥 Request Body

```json
{
  "land_size": 2,
  "income": 100000,
  "crop_type": "wheat",
  "location": "Nashik",
  "season": "rabi"
}
```

---

## 📊 Request Fields

| Field     | Type   | Required | Description                  |
| --------- | ------ | -------- | ---------------------------- |
| land_size | float  | ✅        | Land holding in acres        |
| income    | float  | ✅        | Annual income in ₹           |
| crop_type | string | ✅        | Crop name                    |
| location  | string | ✅        | District (e.g. Nashik, Pune) |
| season    | string | ✅        | `kharif` or `rabi`           |

---

## 📤 Response Format

```json
{
  "schemes": [
    {
      "scheme": "PMFBY",
      "confidence": 99,
      "eligibility": "Highly Eligible",
      "documents_required": ["Aadhaar Card", "Crop Details"],
      "description": "Crop insurance scheme...",
      "location_boost": "Nashik adjustment (x1.15)",
      "boost_reason": "High crop loss risk → Insurance prioritized",
      "explanation": "Adjusted based on HIGH risk in Nashik"
    }
  ],
  "recommendations": [
    "For PM-KISAN: reduce declared income by ₹100,000 to qualify"
  ]
}
```

---

# 🧠 How Scoring Works

The system combines multiple intelligent layers:

### 1. Base Matching

* Land ≤ max_land
* Income ≤ max_income
* Crop compatibility

---

### 2. ML Prediction

* RandomForest model predicts eligibility probability

---

### 3. Calibration Layer

* Small farmers → boosted schemes
* High income → penalties
* Crop relevance adjustments

---

### 4. Seasonal Filtering

* Only schemes valid for selected season are considered

---

### 5. Location Weighting

Example:

* Nashik → drought schemes boosted
* Kolhapur → drought schemes reduced

---

### 6. Risk Integration

Uses crop risk model:

* HIGH risk → boosts:

  * PMFBY (insurance)
  * DroughtRelief
* Other schemes slightly reduced

---

### 7. Final Ranking

Sorted by confidence score (descending)

---

# 🎯 Confidence Levels

| Score Range | Label               |
| ----------- | ------------------- |
| ≥ 80        | Highly Eligible     |
| 60–79       | Moderately Eligible |
| < 60        | Low Eligibility     |

---

# 💡 Recommendations Engine

Suggests how to become eligible for more schemes.

### Example:

```
For NMSA: reduce land by 2 acres (max 3 acres), reduce declared income by ₹150,000
```

### Logic:

* Calculates **exact gap**
* Prioritizes easiest changes first

---

# ⚠️ Edge Cases

### ❌ Invalid Crop

```json
{
  "schemes": [],
  "message": "No schemes available for crop 'xyz'"
}
```

---

### ❌ No Recommendations

```json
"recommendations": [
  "You are eligible for all available schemes."
]
```

---

### ⚠️ Unknown District

* No crash
* Default weights applied

---

# 📋 Supported Crops

* wheat
* rice
* cotton
* soybean
* sugarcane

---

# 🏛️ Available Schemes

| Scheme        | Description                |
| ------------- | -------------------------- |
| PM-KISAN      | Direct income support      |
| PMFBY         | Crop insurance             |
| SoilHealth    | Soil testing               |
| KCC           | Agricultural credit        |
| NMSA          | Sustainable farming        |
| DroughtRelief | Drought compensation       |
| OrganicScheme | Organic farming support    |
| PMKSY         | Irrigation support         |
| RKVY          | Infrastructure development |
| NFSM          | Food security mission      |
| PKVY          | Organic cluster farming    |
| eNAM          | Online market platform     |

---

# 🔄 Related APIs

## 🌧 Crop Risk

### POST `/api/crop-risk`

Predicts crop loss probability.

---

## 📍 District Risks

### GET `/api/district-risks`

Returns district-wise risk data.

---

## 📊 Eligibility Summary

### GET `/api/eligibility-summary`

Returns:

* Avg schemes per farmer
* Most common scheme

---

# 🧪 Example cURL

```bash
curl -X POST http://localhost:8000/api/eligibility \
-H "Content-Type: application/json" \
-d '{
  "land_size": 1.5,
  "income": 80000,
  "crop_type": "wheat",
  "location": "Nashik",
  "season": "rabi"
}'
```

---

# 📌 Notes for Integration

* Always pass `season`
* Crop must be lowercase
* Location should match known districts
* Response always contains:

  * `schemes`
  * `recommendations`

---

# ✅ Summary

This API provides:

* Intelligent scheme matching
* Risk-aware prioritization
* Location & seasonal awareness
* Actionable recommendations

👉 Designed for **real-world agricultural decision support**
