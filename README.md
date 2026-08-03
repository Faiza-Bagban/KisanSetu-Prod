# 🌾 KisanSetu — Intelligent Agriculture Administration System

> **v1.0.0** · Pune Agri Hackathon 2026 · Team: Faiza Bagban + Sakshi Kolhe

KisanSetu is a full-stack AI-powered platform that helps Maharashtra's
agriculture administration process farmer documents, route grievances,
assess crop-loss risk, and check government scheme eligibility — all in
one system, using real satellite/weather data and real AI reasoning
instead of hardcoded rules.

---

## 🚀 Live

| Service | URL |
|---|---|
| **Frontend (production)** | https://kisansetu-six.vercel.app |
| **Backend API (Docker, full features)** | https://kisansetu-prod-backend-docker.onrender.com/docs |
| **Login** | `admin@kisansetu.gov` / `password123` |

> **Free-tier note:** both services spin down after inactivity — first
> request may take ~50s to wake up.

---

## ✨ Features

All features are live and confirmed working end-to-end in production.

| Feature | What it does |
|---|---|
| **Crop-Loss Risk Prediction** | XGBoost model on real IMD (rainfall/temperature), NASA MODIS NDVI, and NASA POWER (soil moisture) data. Cross-validated, versioned, auto-retrainable in one command. |
| **AI Scheme Eligibility** | LLM reasoning (Groq API) over 8 individually researched, real government scheme criteria — not hardcoded thresholds, which were found to misclassify most farmers. |
| **RAG Chatbot** | Multilingual (English/Hindi/Marathi) assistant grounded in real scheme documents and live crop-risk data via ChromaDB retrieval + Groq generation. |
| **Grievance Classification** | Dual-mode AI classifier — full neural zero-shot model, or a genuinely lightweight fallback for constrained hosting — with real database-backed duplicate detection and audit logging. |
| **OCR / Document Processing (IDP)** | Multilingual (English/Marathi/Hindi) document extraction via Tesseract + OpenCV preprocessing, with real database-backed approve/flag workflow. |
| **Auth & RBAC** | JWT access/refresh tokens, role-based access (farmer/field officer/district officer/admin), rate limiting. |
| **Dashboards** | Risk map (Leaflet + NDVI), grievance/audit dashboards, intelligence report with live district data. |

---

## 🏗️ Architecture

```
frontend/          React + Vite (Leaflet maps, Recharts, chatbot widget)
backend/
  routes/          FastAPI endpoints (auth, IDP, grievance, eligibility,
                    chatbot, crop-loss, admin/dashboard)
  modules/         AI/ML logic:
                      idp.py              — OCR + field extraction
                      grievance.py        — dual-mode classifier
                      lightweight_classifier.py — TF-IDF fallback
                      crop_loss.py        — XGBoost risk model
                      eligibility_ai.py   — Groq LLM reasoning
                      rag_chatbot.py      — ChromaDB + Groq RAG pipeline
                      translation.py      — MarianMT (Hindi/Marathi)
                      model_registry.py   — lightweight model versioning
  models/          SQLAlchemy DB models
  scripts/         Data fetch scripts (IMD/NDVI/soil moisture) +
                    retrain_pipeline.py (one-command full retrain)
  data/            Real processed datasets, real scheme criteria text
  saved_models/    Trained model artifacts + version registry
  tests/           pytest suite (35+ tests, CI green)
.github/workflows/ GitHub Actions CI
```

**Key design decisions, briefly:**
- **Eligibility uses LLM reasoning, not hardcoded rules** — most real
  government schemes (PM-KISAN, PMFBY, KCC) don't use simple numeric
  thresholds; a rules-based system was found to give wrong answers.
- **Grievance classification is dual-mode** — a full neural classifier for
  accuracy on resource-rich hosting, and a genuinely tiny TF-IDF model
  (~57KB) for memory-constrained free-tier hosting, switchable via env var.
- **LLM/embedding calls use hosted APIs (Groq, Hugging Face)**, not a
  local model — this was a deliberate migration after hitting a real
  512MB memory ceiling on free-tier hosting; see `docs/changelog.md`.
- **The OCR-capable backend runs on Docker**, not Render's native Python
  runtime — Tesseract is a system-level dependency that native runtimes
  can't install; Docker is required for it.

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Tesseract OCR (with `mar` + `hin` language packs)
- Poppler (for PDF processing)
- Node.js 18+
- A free [Groq](https://console.groq.com) API key
- A free [Hugging Face](https://huggingface.co/settings/tokens) token
  (needs the **"Inference"** permission preset)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
python -m pip install -r ../requirements.txt
python -m pip install -r requirements.txt

# Create .env from example, then fill in real values
cp .env.example .env
```

Required `.env` variables:
```
SECRET_KEY=<a long random string>
DATABASE_URL=postgresql://user:password@localhost:5432/kisansetu
GROQ_API_KEY=<your Groq API key>
HF_TOKEN=<your Hugging Face token, "Inference" permission>
GRIEVANCE_CLASSIFIER=zero_shot   # or "lightweight" for constrained hosting
```

```bash
# Create DB
psql -U postgres -c "CREATE DATABASE kisansetu;"

# Run (seeds automatically on first startup)
python -m uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env — set VITE_API_BASE to your backend URL
npm run dev
```

---

## 🐳 Docker

```bash
cd backend
docker build -t kisansetu-backend -f Dockerfile ..
docker run -p 8000:8000 --env-file .env kisansetu-backend
```

The Docker image includes Tesseract, Poppler, and pre-caches/trains all
ML models at build time (grievance classifier, crop-loss model) so the
container starts ready to serve, without first-request delays.

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v --ignore=tests/test_eligibility.py
```

CI runs the full suite automatically on every push/PR via GitHub Actions,
using a real ephemeral PostgreSQL service container (not mocked). The
eligibility test file needs external network access it can't rely on in
CI and is run manually.

---

## 🔁 Retraining the Crop-Loss Model

```bash
python backend/scripts/retrain_pipeline.py
```

One command: re-fetches IMD rainfall/temperature, NASA NDVI, and NASA
POWER soil-moisture data, rebuilds the merged training dataset, retrains
the model, and logs a new version to `saved_models/registry.json`.

---


## 👥 Team

| Person | Focus |
|---|---|
| **Faiza Bagban** | Repo owner — crop-loss model, eligibility AI, RAG chatbot, grievance classification,IDP, MLOps (Docker, CI, retrain pipeline, model versioning), staging/production deployment |
| **Sakshi Kolhe** | OCR, auth & RBAC, audit logging, dashboards, testing, frontend (React), Vercel deployment |

---

## 📁 Key Docs

- `docs/model-card-crop-loss.md` — crop-loss model data sources, label, limitations
- `docs/model-card-eligibility.md` — eligibility engine design rationale
- `docs/modules-guide-faiza.md` — setup/usage guide for AI modules
- `docs/changelog.md` — full project history, including the memory-constraint migration
- `docs/bug_list.md` — known issues log
- `docs/demo_script.md` — walkthrough script for demos
- `docs/deployment_checklist.md` — deployment checklist
- `docs/staging_test_results.md` — staging test report
- `backend/.env.example`, `frontend/.env.example` — required env vars
