"""
Automation API routes for all 5 KisanSetu automations.
Prefix: /api  (no sub-prefix, matches the existing pattern)
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from auth.role_checker import RoleChecker
from database import get_db
from models.systemic_issue_model import SystemicIssue
from models.proactive_alert_model import ProactiveAlert
from models.relief_case_model import ReliefCase
from models.officer_score_model import OfficerScore

from automation.systemic_detector import detect_systemic_issues
from automation.seasonal_intelligence import generate_seasonal_alerts
from automation.relief_pipeline import advance_pipeline_stage
from automation.officer_scorecard import compute_officer_scores

router = APIRouter()

allow_officer = RoleChecker(["field_officer", "district_officer", "admin"])
allow_admin   = RoleChecker(["admin"])


# ════════════════════════════════════════════════
# AUTOMATION 2 — SYSTEMIC ISSUES
# ════════════════════════════════════════════════

@router.get("/api/systemic-issues")
def get_systemic_issues(
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    district = officer.get("district", "All")
    query = db.query(SystemicIssue)
    if district.lower() != "all":
        query = query.filter(SystemicIssue.district == district)
    issues = query.order_by(SystemicIssue.detected_at.desc()).all()
    return [
        {
            "id": i.id,
            "district": i.district,
            "category": i.category,
            "farmer_count": i.farmer_count,
            "grievance_ids": json.loads(i.individual_grievance_ids or "[]"),
            "status": i.status,
            "detected_at": i.detected_at.isoformat() if i.detected_at else None,
        }
        for i in issues
    ]


class SystemicStatusUpdate(BaseModel):
    status: str  # open | investigating | resolved


@router.patch("/api/systemic-issues/{issue_id}/status")
def update_systemic_status(
    issue_id: int,
    req: SystemicStatusUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(allow_officer),
):
    valid = {"open", "investigating", "resolved"}
    if req.status not in valid:
        raise HTTPException(400, f"Status must be one of: {', '.join(valid)}")
    issue = db.query(SystemicIssue).filter(SystemicIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Systemic issue not found")
    issue.status = req.status
    db.commit()
    return {"id": issue_id, "status": req.status}


@router.post("/api/systemic-issues/detect")
def trigger_detection(_: dict = Depends(allow_admin)):
    detect_systemic_issues()
    return {"message": "Systemic issue detection triggered"}


# ════════════════════════════════════════════════
# AUTOMATION 3 — PROACTIVE ALERTS
# ════════════════════════════════════════════════

@router.get("/api/alerts")
def get_alerts(
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    district = officer.get("district", "All")
    query = db.query(ProactiveAlert)
    if district.lower() != "all":
        query = query.filter(ProactiveAlert.district == district)
    alerts = (
        query
        .order_by(
            ProactiveAlert.priority.desc(),
            ProactiveAlert.created_at.desc(),
        )
        .all()
    )
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    result = sorted(
        [
            {
                "id": a.id,
                "district": a.district,
                "crop": a.crop,
                "alert_type": a.alert_type,
                "message": a.message,
                "priority": a.priority,
                "is_read": a.is_read,
                "auto_generated": a.auto_generated,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        key=lambda x: priority_order.get(x["priority"], 99),
    )
    return result


@router.patch("/api/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(allow_officer),
):
    alert = db.query(ProactiveAlert).filter(ProactiveAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_read = True
    db.commit()
    return {"id": alert_id, "is_read": True}


@router.post("/api/alerts/generate")
def generate_alerts(_: dict = Depends(allow_admin)):
    generate_seasonal_alerts()
    return {"message": "Seasonal alerts generated"}


# ════════════════════════════════════════════════
# AUTOMATION 4 — RELIEF PIPELINE
# ════════════════════════════════════════════════

@router.get("/api/relief-cases")
def get_relief_cases(
    db: Session = Depends(get_db),
    officer: dict = Depends(allow_officer),
):
    district = officer.get("district", "All")
    query = db.query(ReliefCase)
    if district.lower() != "all":
        query = query.filter(ReliefCase.district == district)
    cases = query.order_by(ReliefCase.triggered_at.desc()).all()
    return [
        {
            "id": c.id,
            "district": c.district,
            "crop": c.crop,
            "risk_percent": c.risk_percent,
            "triggered_by": c.triggered_by,
            "pipeline_stage": c.pipeline_stage,
            "stage_deadline": c.stage_deadline.isoformat() if c.stage_deadline else None,
            "assigned_officer": c.assigned_officer,
            "farmer_count_affected": c.farmer_count_affected,
            "pmfby_claim_initiated": c.pmfby_claim_initiated,
            "status": c.status,
            "triggered_at": c.triggered_at.isoformat() if c.triggered_at else None,
        }
        for c in cases
    ]


class PipelineAdvanceRequest(BaseModel):
    action: str          # approve | reject
    note: Optional[str] = ""


@router.post("/api/relief-cases/{case_id}/advance")
def advance_case(
    case_id: int,
    req: PipelineAdvanceRequest,
    officer: dict = Depends(allow_officer),
):
    if req.action not in {"approve", "reject"}:
        raise HTTPException(400, "action must be 'approve' or 'reject'")
    result = advance_pipeline_stage(
        case_id, req.action, officer.get("sub", "officer"), req.note or ""
    )
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/api/relief-cases/{case_id}/audit")
def get_case_audit(
    case_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(allow_officer),
):
    case = db.query(ReliefCase).filter(ReliefCase.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found")
    return {
        "id": case_id,
        "district": case.district,
        "pipeline_stage": case.pipeline_stage,
        "status": case.status,
        "audit_trail": json.loads(case.audit_trail or "[]"),
    }


class ManualTriggerRequest(BaseModel):
    district: str
    crop: str
    risk_percent: float


@router.post("/api/relief-cases/trigger")
def trigger_relief(
    req: ManualTriggerRequest,
    _: dict = Depends(allow_officer),
):
    from automation.relief_pipeline import auto_trigger_relief_pipeline
    auto_trigger_relief_pipeline(req.district, req.crop, {"risk_percent": req.risk_percent})
    return {"message": f"Relief pipeline triggered for {req.district}/{req.crop}"}


# ════════════════════════════════════════════════
# AUTOMATION 5 — OFFICER SCORES
# ════════════════════════════════════════════════

@router.get("/api/officer-scores")
def get_officer_scores(
    db: Session = Depends(get_db),
    _: dict = Depends(allow_admin),
):
    scores = db.query(OfficerScore).order_by(OfficerScore.score.desc()).all()
    return [
        {
            "id": s.id,
            "officer_id": s.officer_id,
            "officer_name": s.officer_name,
            "district": s.district,
            "total_grievances": s.total_grievances,
            "resolved_count": s.resolved_count,
            "avg_days": s.avg_days,
            "escalation_count": s.escalation_count,
            "sla_compliant_count": s.sla_compliant_count,
            "score": s.score,
            "grade": s.grade,
            "computed_at": s.computed_at.isoformat() if s.computed_at else None,
        }
        for s in scores
    ]


@router.get("/api/officer-scores/{officer_id}")
def get_officer_score(
    officer_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(allow_admin),
):
    s = db.query(OfficerScore).filter(OfficerScore.officer_id == officer_id).first()
    if not s:
        raise HTTPException(404, "Officer score not found")
    return {
        "officer_id": s.officer_id,
        "officer_name": s.officer_name,
        "district": s.district,
        "total_grievances": s.total_grievances,
        "resolved_count": s.resolved_count,
        "avg_days": s.avg_days,
        "escalation_count": s.escalation_count,
        "score": s.score,
        "grade": s.grade,
    }


@router.post("/api/officer-scores/refresh")
def refresh_scores(_: dict = Depends(allow_admin)):
    compute_officer_scores()
    return {"message": "Officer scores recomputed"}
