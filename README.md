# 🌾 KisanSetu — Intelligent Agriculture Administration System

> Pune Agri Hackathon 2026 · Team: Faiza Bagban + Sakshi Kolhe

KisanSetu is a full-stack AI-powered platform that helps Maharashtra's agriculture administration process farmer documents, route grievances, assess crop-loss risk, and check scheme eligibility — all in one system.

---

## 🚀 Live Staging

| Service | URL |
|---------|-----|
| Backend API | https://kisansetu-prod-backend.onrender.com/docs |
| Login | admin@kisansetu.gov / password123 |

> **Note:** Free tier spins down after inactivity — first request may take ~50s.  
> Eligibility AI and chatbot show graceful "unavailable" on staging (require local GPU/Ollama).

---

## 🏗️ Architecture

```
frontend/          React + Vite (Leaflet maps, Recharts, Tailwind)
backend/
  routes/          FastAPI endpoints (auth, IDP, grievance, eligibility, dashboard)
  modules/         ML + OCR logic (idp.py, grievance.py, crop_loss.py, eligibility_ai.py)
  models/          SQLAlchemy DB models
  data/processed/  Real 2024 crop-loss merged dataset (IMD + NASA POWER + NDVI)
  tests/           pytest suite (46 tests, CI green)
.github/workflows/ GitHub Actions CI
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 17
- Tesseract OCR (with `mar` + `hin` language packs)
- Poppler (for PDF processing)
- Node.js 18+

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env — set DATABASE_URL and SECRET_KEY

# Create DB
psql -U postgres -c "CREATE DATABASE kisansetu;"

# Seed demo data
python seed_db.py

# Run
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install

# Create .env from example
cp .env.example .env
# Edit .env — set VITE_API_BASE=http://localhost:8000

npm run dev
```

### Windows PATH setup (required each terminal session)
```powershell
$env:Path += ";C:\Program Files\PostgreSQL\17\bin"
$env:Path += ";C:\poppler\poppler-26.02.0\Library\bin"
```

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v --ignore=tests/test_eligibility.py
# 46 passed, 2 skipped — eligibility tests require Ollama + llama3.1:8b
```

---

## 🔑 Key Features

| Feature | Owner | Status |
|---------|-------|--------|
| OCR/IDP — multilingual (English + Marathi + Hindi) | Sakshi | ✅ |
| JWT auth + rate limiting + RBAC | Sakshi | ✅ |
| Audit logging | Sakshi | ✅ |
| Dashboard — NDVI map + Recharts risk charts | Sakshi | ✅ |
| Crop-loss risk prediction (XGBoost, real 2024 data) | Faiza | ✅ |
| Scheme eligibility AI (Ollama/llama3.1) | Faiza | ✅ (local GPU only) |
| RAG chatbot (multilingual) | Faiza | ✅ (local GPU only) |
| Grievance classification (XLM-RoBERTa) | Faiza | ✅ |
| GitHub Actions CI | Faiza + Sakshi | ✅ green |
| Staging deployment (Render) | Faiza | ✅ |

---

## 👥 Team

| Person | Role | Hardware |
|--------|------|----------|
| Faiza Bagban | Repo owner, ML/GPU work | RTX 5070 8GB |
| Sakshi Kolhe | OCR, auth, dashboard, testing | Intel UHD (CPU only) |

---

## 📁 Key Docs

- `docs/bug_list.md` — known issues
- `docs/ocr_audit_log.md` — OCR failure case history
- `docs/staging_test_results.md` — staging test report
- `docs/deployment_checklist.md` — deployment checklist
- `backend/.env.example` — required env vars
- `frontend/.env.example` — required frontend env vars