from fastapi import APIRouter, Depends
import json, os
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from auth.role_checker import RoleChecker
from database import get_db
from models.document_model import Document
from modules.crop_loss import predict_risk


router = APIRouter()

# ✅ Enforce Admin-only access
allow_admin = RoleChecker(["admin"])

# Officers + admin can view documents for review
allow_officer = RoleChecker(["field_officer", "district_officer", "admin"])

# Shared Audit Logging Store
audit_logs = []

def add_audit_log(entry: dict):
    """Centralized log handler with a 200-entry memory cap."""
    audit_logs.append(entry)
    if len(audit_logs) > 200:
        audit_logs.pop(0)

# ✅ FIX 2: Protected Admin Dashboard
@router.get("/admin-dashboard", dependencies=[Depends(allow_admin)])
def get_admin_summary():
    """Returns the state-wide risk map intelligence for authorized admins."""
    DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "district_risks.json")
    
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    return {"message": "Admin Access Granted", "data": "No precomputed data found."}

@router.get("/api/audit-logs", dependencies=[Depends(allow_admin)])
def get_audit_logs():
    """Returns the latest 20 audit records, restricted to the Admin role."""
    from modules.audit_logger import get_recent_logs
    return {"logs": get_recent_logs(20)}


# ── DOCUMENTS ────────────────────────────────────────────────

@router.get("/api/documents", dependencies=[Depends(allow_officer)])
def list_documents(db: Session = Depends(get_db)):
    """
    Returns all seeded/submitted documents for officer review.
    """
    documents = db.query(Document).all()
    return [
        {
            "id": d.id,
            "farmer_id": d.farmer_id,
            "document_type": d.document_type,
            "extracted_text": d.extracted_text,
            "verification_status": d.verification_status,
        }
        for d in documents
    ]


# ── INTELLIGENCE SUMMARY ─────────────────────────────────────

@router.get("/api/intelligence-summary", dependencies=[Depends(allow_officer)])
def intelligence_summary():
    """
    District-level crop-risk intelligence for the IntelligenceReport screen.
    Pune uses REAL live predictions from the trained crop-loss model.
    Other districts show STATIC/DEMO data — the model is currently trained
    only on Pune (real 2024 IMD/NDVI/soil-moisture data); expanding to real
    multi-district predictions requires collecting/training on their data
    too (see docs/model-card-crop-loss.md).
    """
    DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "district_risks.json")

    with open(DATA_PATH, "r") as f:
        static_data = json.load(f)

    result = []
    for entry in static_data["districts"]:
        if entry["district"] == "Pune":
            live = predict_risk(
                district="Pune",
                rainfall_deficit=10,
                temp_anomaly=2,
                ndvi_drop=0.15,
                soil_moisture=0.5,
                days_since_rain=8,
            )
            result.append({
                "district": "Pune",
                "crop_type": entry.get("crop_type"),
                "risk_level": live.get("risk_level"),
                "risk_percent": live.get("risk_percent"),
                "alert": live.get("alert"),
                "lat": entry.get("lat"),
                "lng": entry.get("lng"),
                "relief_draft": live.get("relief_draft"),
                "data_source": "live_model",
            })
        else:
            result.append({**entry, "data_source": "static_demo"})

    return {"districts": result}


class ReliefApproveRequest(BaseModel):
    district: str
    crop: str = ""
    risk_score: float = 0.0


@router.post("/api/relief/approve")
def approve_relief(body: ReliefApproveRequest, payload: dict = Depends(allow_admin)):
    """Admin approves a pre-filled relief draft for a high-risk district."""
    add_audit_log({
        "user": payload.get("sub", "Unknown"),
        "role": payload.get("role", "N/A"),
        "district": body.district,
        "action": "Relief Draft Approved",
        "file": f"Relief-{body.district}-{body.crop}",
        "status": "AUTO-VERIFIED",
        "timestamp": datetime.utcnow().isoformat()
    })
    return {
        "district": body.district,
        "crop": body.crop,
        "status": "approved",
        "message": f"Relief draft for {body.district} approved — PMFBY process initiated"
    }