from fastapi import APIRouter, Depends
import json, os
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from auth.role_checker import RoleChecker
from database import get_db
from models.document_model import Document


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