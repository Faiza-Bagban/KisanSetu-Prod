from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

# ML Imports
from modules.grievance import classify_grievance
from fastapi.openapi.utils import get_openapi

from sqlalchemy import text
from database import engine, Base

from auth.role_checker import RoleChecker

# SQLAlchemy Models
from models.user_model import User
from models.farmer_model import Farmer
from models.grievance_model import Grievance
from models.scheme_model import Scheme
from models.document_model import Document
from models.audit_model import AuditLog
from models.systemic_issue_model import SystemicIssue
from models.proactive_alert_model import ProactiveAlert
from models.relief_case_model import ReliefCase
from models.officer_score_model import OfficerScore

# Internal Route Imports
from routes import (
    grievance_route,
    eligibility_route,
    idp_route,
    auth_route,
    admin_route,
    crop_loss_route,
    chatbot_route
)
from routes.automation_route import router as automation_router

# ── DB MIGRATION ─────────────────────────────────────────────

def run_grievance_migration():
    """
    Safely adds new columns to the grievances table if they don't exist yet.
    Uses PostgreSQL's 'ADD COLUMN IF NOT EXISTS' so it is idempotent.
    Also copies legacy column data (grievance_text->text, assigned_officer->routed_officer).
    """
    statements = [
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS farmer_id VARCHAR",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS text VARCHAR",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS translated_text VARCHAR",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS confidence FLOAT",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS routed_officer VARCHAR",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS sla_deadline TIMESTAMPTZ",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 0",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS escalation_reason VARCHAR",
        "ALTER TABLE grievances ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ",
        "UPDATE grievances SET text = grievance_text WHERE text IS NULL AND grievance_text IS NOT NULL",
        "UPDATE grievances SET routed_officer = assigned_officer WHERE routed_officer IS NULL AND assigned_officer IS NOT NULL",
        "UPDATE grievances SET status = 'Under Review' WHERE status IS NULL",
        "UPDATE grievances SET escalation_level = 0 WHERE escalation_level IS NULL",
        "UPDATE grievances SET sla_deadline = created_at + INTERVAL '3 days' WHERE sla_deadline IS NULL AND created_at IS NOT NULL",
    ]
    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
        conn.commit()


@asynccontextmanager
async def lifespan(app):
    # Startup
    run_grievance_migration()
    try:
        from seed_db import seed_database
        seed_database()
    except Exception as e:
        print(f"[SEED_DB] Error: {e}")
    try:
        from automation.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[SCHEDULER] Could not start: {e}")
    try:
        from seed_demo import maybe_seed
        maybe_seed()
    except Exception as e:
        print(f"[SEED] Error: {e}")
    yield
    # Shutdown
    try:
        from automation.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception as e:
        print(f"[SCHEDULER] Shutdown error: {e}")


app = FastAPI(
    title="KisanSetu API",
    description="Intelligent Agriculture Administration System for Pune Agri Hackathon 2026",
    version="1.0.4",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://kisansetu-six.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting setup (Week 3 Day 1 - Sakshi)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Base.metadata.create_all(bind=engine)

# Shared auth dependency for top-level routes defined directly in main.py
allow_authenticated_main = RoleChecker(["admin", "farmer", "field_officer", "district_officer"])

# ── ROUTER REGISTRATION ──────────────────────────────────────
app.include_router(auth_route.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin_route.router, prefix="/admin", tags=["Admin Services"])
app.include_router(idp_route.router, tags=["IDP Services"])
app.include_router(grievance_route.router)
app.include_router(eligibility_route.router)
app.include_router(automation_router, tags=["Automations"])
app.include_router(crop_loss_route.router, tags=["ML Services"])
app.include_router(chatbot_route.router, tags=["ML Services"])


# ── ROOT ─────────────────────────────────────────────────────

@app.get("/", tags=["System"])
def root():
    """
    Root endpoint to verify API health.
    """
    return {
        "status": "KisanSetu API Online",
        "security": "JWT + RBAC Active",
        "documentation": "/docs",
        "version": "1.0.4"
    }


# ── DISTRICT RISKS ───────────────────────────────────────────

@app.get("/api/district-risks", tags=["Admin Services"], dependencies=[Depends(allow_authenticated_main)])
def district_risks():
    """
    Fetches district crop-risk intelligence.
    """
    path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "district_risks.json"
    )

    if not os.path.exists(path):
        return {"districts": []}

    with open(path, "r") as f:
        return json.load(f)


# ── ELIGIBILITY ANALYTICS ────────────────────────────────────

@app.get("/api/eligibility-summary", tags=["Analytics"], dependencies=[Depends(allow_authenticated_main)])
def eligibility_summary():
    """
    Returns analytics summary for demo dashboards.
    """
    path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "demo_results.json"
    )

    with open(path, "r") as f:
        data = json.load(f)

    total_schemes = set()
    scheme_count = {}
    total_matches = 0

    for farmer in data:
        schemes = farmer["schemes"]
        total_matches += len(schemes)

        for s in schemes:
            total_schemes.add(s["scheme"])
            scheme_count[s["scheme"]] = (
                scheme_count.get(s["scheme"], 0) + 1
            )

    avg_matches = total_matches / len(data)
    most_common = max(scheme_count, key=scheme_count.get)

    return {
        "total_schemes_available": len(total_schemes),
        "average_matches_per_farmer": round(avg_matches, 2),
        "most_common_scheme": most_common
    }


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}

    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
    # Don't overwrite per-route security requirements (e.g. auto-detected
    # HTTPBearer from role_checker.py) — just add BearerAuth as an option.

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi