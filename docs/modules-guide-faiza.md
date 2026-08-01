# Faiza's Modules — Setup & Usage Guide

Covers: Crop-Loss Risk Prediction, AI Eligibility Engine, RAG Chatbot,
Grievance Module (dual-classifier).

---

## 1. Crop-Loss Risk Prediction

**Endpoint:** `POST /api/crop-loss` (requires auth)

**Request:**
```json
{
  "district": "Pune",
  "rainfall_deficit": 10,
  "temp_anomaly": 2,
  "ndvi_drop": 0.2,
  "soil_moisture": 0.5,
  "days_since_rain": 5
}
```

**Retrain:** `python backend/scripts/retrain_pipeline.py` — re-fetches all
real data (IMD rainfall/temp, NDVI, soil moisture) and retrains in one
command. Takes several minutes.

**See:** `docs/model-card-crop-loss.md` for data sources and limitations.

---

## 2. AI Eligibility Engine

**Endpoint:** `POST /api/eligibility-ai` (requires auth)

**Requires:** Ollama running locally with `llama3.1:8b` pulled
(`ollama pull llama3.1:8b`). Not available on constrained hosting
without GPU — degrades gracefully with an "unavailable" message there.

**Request:**
```json
{
  "land_size": 2,
  "income": 150000,
  "crop_type": "wheat",
  "district": "Pune",
  "is_govt_employee": false,
  "pays_income_tax": false
}
```

**Update scheme criteria:** edit `backend/data/schemes_real.py` directly
(plain text, no retraining needed).

**See:** `docs/model-card-eligibility.md` for scheme research and why
hardcoded thresholds were replaced.

---

## 3. RAG Chatbot

**Module:** `backend/modules/rag_chatbot.py` (no route wired yet —
Sakshi/whoever builds the frontend widget should add
`POST /api/chatbot` calling `chatbot_answer(query)`)

**Setup:** requires Ollama + the same vector store as eligibility.
Build/refresh the vector store:
```python
from modules.rag_chatbot import build_vector_store
build_vector_store()
```
This embeds all scheme documents plus live crop-risk data for known
districts. Re-run after updating `schemes_real.py`.

**Usage:**
```python
from modules.rag_chatbot import chatbot_answer
result = chatbot_answer("What crop insurance schemes are available?")
# {"answer": "...", "detected_language": "en", "sources": [...]}
```

Supports English, Hindi, and Marathi — detects language, retrieves in
English, generates natively in the detected language (not machine-
translated, which produced worse results in testing).

---

## 4. Grievance Module (Dual-Classifier)

**Endpoint:** `POST /api/grievance` (requires auth)

**Two classifier modes**, switchable via `GRIEVANCE_CLASSIFIER` env var:
- `zero_shot` (default) — BART/DistilBART neural classifier, more
  accurate, needs ~500MB+ RAM. Use for local dev or resource-rich hosting.
- `lightweight` — TF-IDF + Logistic Regression, ~57KB total, needs
  `GRIEVANCE_CLASSIFIER=lightweight` set. Use for constrained hosting
  (e.g. Render free tier). Trained on a small synthetic dataset — see
  `backend/scripts/build_grievance_training_data.py`.

**Retrain lightweight classifier** (after editing training data):
```powershell
python -m modules.lightweight_classifier
```

**Real fixes made to this module:**
- Duplicate-check was a hardcoded fake list — now queries the real DB
- Marathi keyword hints no longer silently override real classification
- Fixed category-name mismatch (underscores vs spaces) that broke
  drought/flood/disease/irrigation-specific routing
- Added Hindi keywords alongside existing Marathi/English

---

## Environment Variables (my modules)

| Variable | Purpose | Required for |
|---|---|---|
| `GRIEVANCE_CLASSIFIER` | `zero_shot` or `lightweight` | Grievance module |
| (Ollama running locally) | LLM reasoning + chat generation | Eligibility, Chatbot |