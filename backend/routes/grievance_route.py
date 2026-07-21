from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone, timedelta

from auth.role_checker import RoleChecker
from database import get_db
from models.grievance_model import Grievance
from models.audit_model import AuditLog
from modules.grievance import classify_grievance
from experimental.grievance_crossmodule import get_suggested_action
from automation.escalation_engine import FIELD_OFFICER_SLA_DAYS

router = APIRouter()

# ── ROLE DEFINITIONS ────────────────────────────────────────
allow_farmer = RoleChecker(["farmer", "admin"])
allow_officer = RoleChecker(["field_officer", "district_officer", "admin"])

# ── OFFICER ROUTING MAP ─────────────────────────────────────
OFFICER_MAP = {
    "payment_issue":      "District Finance Officer",
    "scheme_delay":       "Scheme Coordinator",
    "document_rejection": "District Agriculture Officer",
    "officer_misconduct": "Vigilance Officer",
    "other":              "District Agriculture Officer",
}

# ── HELPERS ──────────────────────────────────────────────────

def normalize_category(cat: str) -> str:
    """Convert space-separated category names to underscore form."""
    return cat.lower().replace(" ", "_")


def extract_days(resolution_time) -> int:
    """Parse '8 working days' → 8, with a safe fallback."""
    try:
        return int(str(resolution_time).split()[0])
    except (ValueError, IndexError, AttributeError):
        return 7


# ── REQUEST MODELS ───────────────────────────────────────────

class GrievanceRequest(BaseModel):
    text: str
    farmer_id: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    status: str  # "Under Review" | "Resolved" | "Escalated"


class EscalateRequest(BaseModel):
    reason: Optional[str] = ""


# ── ANALYTICS  (must be registered before /{grievance_id}) ──

@router.get("/api/grievance/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    _: dict = Depends(allow_officer),
):
    """
    Returns aggregate stats computed from DB.
    Restricted to officers and admins.
    """
    all_grievances = db.query(Grievance).all()
    total = len(all_grievances)
    open_count = sum(1 for g in all_grievances if g.status != "Resolved")
    resolved_count = sum(1 for g in all_grievances if g.status == "Resolved")
    avg_resolution_days = (
        round(
            sum(g.resolution_days or 7 for g in all_grievances) / total, 1
        )
        if total > 0
        else 0
    )

    category_breakdown = {
        "payment_issue": 0,
        "scheme_delay": 0,
        "document_rejection": 0,
        "officer_misconduct": 0,
        "other": 0,
    }
    for g in all_grievances:
        cat = normalize_category(g.category or "other")
        if cat in category_breakdown:
            category_breakdown[cat] += 1
        else:
            category_breakdown["other"] += 1

    return {
        "total": total,
        "open_count": open_count,
        "resolved_count": resolved_count,
        "avg_resolution_days": avg_resolution_days,
        "category_breakdown": category_breakdown,
    }


# ── LIST ALL GRIEVANCES ──────────────────────────────────────

@router.get("/api/grievance")
def list_grievances(
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    """
    Returns all grievances for the officer's jurisdiction.
    District Officers and Admins with 'All' jurisdiction see every record.
    """
    district = officer.get("district", "All")
    query = db.query(Grievance)
    if district and district.lower() != "all":
        query = query.filter(Grievance.jurisdiction == district)

    grievances = query.order_by(Grievance.created_at.desc()).all()
    return [
        {
            "id": g.id,
            "farmer_id": g.farmer_id,
            "text": g.text,
            "translated_text": g.translated_text,
            "category": g.category,
            "confidence": g.confidence,
            "resolution_days": g.resolution_days,
            "routed_officer": g.routed_officer,
            "status": g.status,
            "jurisdiction": g.jurisdiction,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in grievances
    ]


# ── SUBMIT GRIEVANCE ─────────────────────────────────────────

@router.post("/api/grievance")
def analyze_grievance(
    req: GrievanceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(allow_farmer),
):
    """
    Farmers/Admins submit a grievance.
    Runs xlm-roberta zero-shot classification, saves result to DB.
    """
    result = classify_grievance(req.text)

    cat = normalize_category(result.get("category", "other"))
    days = extract_days(result.get("resolution_time", "7 working days"))
    officer = OFFICER_MAP.get(cat, "District Agriculture Officer")
    jurisdiction = current_user.get("district", "Pune")

    suggested_action = get_suggested_action(
    jurisdiction,
    cat
)

    grievance = Grievance(
        farmer_id=req.farmer_id or current_user.get("sub"),
        text=req.text,
        translated_text=result.get("translated_text"),
        category=cat,
        confidence=result.get("confidence"),
        resolution_days=days,
        routed_officer=officer,
        status="Under Review",
        jurisdiction=jurisdiction,
        sla_deadline=datetime.now(timezone.utc) + timedelta(days=FIELD_OFFICER_SLA_DAYS),
        escalation_level=0,
    )
    db.add(grievance)
    db.commit()
    db.refresh(grievance)

    return {
        "id": grievance.id,
        "grievance_id": f"GRV-2026-{grievance.id:04d}",

        "category": cat,
        "confidence": result.get("confidence"),

        "priority": result.get("priority"),

        "resolution_days": days,

        "routed_officer": officer,

        "assigned_officer": officer,

        "suggested_action": suggested_action,

        "translated_text": result.get("translated_text"),

        "status": grievance.status,
    }



# ── ESCALATED GRIEVANCES ─────────────────────────────────────

@router.get("/api/grievance/escalated")
def get_escalated_grievances(
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    district = officer.get("district", "All")
    query = db.query(Grievance).filter(Grievance.escalation_level > 0)
    if district and district.lower() != "all":
        query = query.filter(Grievance.jurisdiction == district)
    grievances = query.order_by(Grievance.escalation_level.desc(), Grievance.escalated_at.desc()).all()
    return [
        {
            "id": g.id,
            "grievance_id": f"GRV-2026-{g.id:04d}",
            "farmer_id": g.farmer_id,
            "text": g.text,
            "category": g.category,
            "status": g.status,
            "escalation_level": g.escalation_level,
            "escalation_reason": g.escalation_reason,
            "escalated_at": g.escalated_at.isoformat() if g.escalated_at else None,
            "sla_deadline": g.sla_deadline.isoformat() if g.sla_deadline else None,
            "jurisdiction": g.jurisdiction,
            "routed_officer": g.routed_officer,
        }
        for g in grievances
    ]


# ── ESCALATE GRIEVANCE ───────────────────────────────────────

ESCALATION_OFFICERS = {
    1: lambda jurisdiction: f"District Officer - {jurisdiction or 'General'}",
    2: lambda _: "State Agriculture Department",
}

@router.patch("/api/grievance/{grievance_id}/escalate")
def escalate_grievance(
    grievance_id: int,
    req: EscalateRequest,
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    g = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")

    current_level = g.escalation_level or 0
    if current_level >= 2:
        raise HTTPException(
            status_code=400,
            detail="Already at highest escalation level",
        )

    new_level = current_level + 1
    now = datetime.now(timezone.utc)
    new_officer = ESCALATION_OFFICERS[new_level](g.jurisdiction)
    new_deadline = now + timedelta(days=2)

    g.escalation_level = new_level
    g.routed_officer = new_officer
    g.sla_deadline = new_deadline
    g.escalated_at = now
    g.status = "Escalated"
    db.add(g)

    log = AuditLog(
        action=(
            f"Grievance #{grievance_id} manually escalated to level {new_level} "
            f"(reason: {req.reason or 'N/A'})"
        ),
        timestamp=now.isoformat(),
        officer_name=officer.get("sub", "Unknown Officer"),
    )
    db.add(log)
    db.commit()
    db.refresh(g)

    return {
        "id": g.id,
        "grievance_id": f"GRV-2026-{g.id:04d}",
        "status": g.status,
        "escalation_level": g.escalation_level,
        "routed_officer": g.routed_officer,
        "sla_deadline": g.sla_deadline.isoformat() if g.sla_deadline else None,
        "escalated_at": g.escalated_at.isoformat() if g.escalated_at else None,
        "message": f"Escalated to level {new_level}: {new_officer}",
    }


# ── GET SINGLE GRIEVANCE ─────────────────────────────────────

@router.get("/api/grievance/{grievance_id}")
def get_grievance(
    grievance_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(allow_farmer),
):
    """
    Returns a single grievance by numeric ID or GRV-2026-XXXX format.
    Used by the farmer status tracker.
    """
    if grievance_id.upper().startswith("GRV-"):
        try:
            numeric_id = int(grievance_id.split("-")[-1])
        except ValueError:
            raise HTTPException(status_code=404, detail="Grievance not found")
    else:
        try:
            numeric_id = int(grievance_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Grievance not found")

    g = db.query(Grievance).filter(Grievance.id == numeric_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")

    return {
        "id": g.id,
        "grievance_id": f"GRV-2026-{g.id:04d}",
        "farmer_id": g.farmer_id,
        "text": g.text,
        "translated_text": g.translated_text,
        "category": g.category,
        "confidence": g.confidence,
        "resolution_days": g.resolution_days,
        "routed_officer": g.routed_officer,
        "status": g.status,
        "jurisdiction": g.jurisdiction,
        "eta": f"{g.resolution_days or 7} working days",
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


# ── UPDATE GRIEVANCE STATUS ──────────────────────────────────

@router.patch("/api/grievance/{grievance_id}/status")
def update_grievance_status(
    grievance_id: int,
    req: StatusUpdateRequest,
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    """
    Officers update grievance status and log to audit_logs table.
    Accepted values: 'Under Review', 'Resolved', 'Escalated'
    """
    valid_statuses = {"Under Review", "Resolved", "Escalated"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(sorted(valid_statuses))}",
        )

    g = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")

    g.status = req.status
    db.add(g)

    log = AuditLog(
        action=f"Grievance #{grievance_id} status updated to '{req.status}'",
        timestamp=datetime.now(timezone.utc).isoformat(),
        officer_name=officer.get("sub", "Unknown Officer"),
    )
    db.add(log)
    db.commit()

    return {
        "id": grievance_id,
        "status": req.status,
        "message": "Status updated successfully",
    }


# ── RESOLVE GRIEVANCE ────────────────────────────────────────

@router.post("/api/grievance/{grievance_id}/resolve")
def resolve_grievance(
    grievance_id: int,
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    g = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")

    g.status = "Resolved"
    g.resolved_at = datetime.now(timezone.utc)
    db.add(g)

    log = AuditLog(
        action=f"Grievance #{grievance_id} resolved by officer",
        timestamp=datetime.now(timezone.utc).isoformat(),
        officer_name=officer.get("sub", "Unknown Officer"),
    )
    db.add(log)
    db.commit()

    return {
        "id": grievance_id,
        "status": "Resolved",
        "resolved_at": g.resolved_at.isoformat(),
        "message": "Grievance resolved successfully",
    }
