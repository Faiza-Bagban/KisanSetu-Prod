"""
AUTOMATION 4 — Smart Relief Cascade Pipeline
auto_trigger_relief_pipeline() called from /api/crop-risk when risk > 75%.
check_pipeline_deadlines() runs every 60 seconds via APScheduler.
"""
import json
from datetime import datetime, timezone, timedelta

from database import SessionLocal
from models.relief_case_model import ReliefCase
from models.proactive_alert_model import ProactiveAlert
from models.audit_model import AuditLog

RISK_THRESHOLD = 75.0

STAGE_ORDER = [
    "draft_generated",
    "officer_review",
    "survey_scheduled",
    "claim_initiated",
    "completed",
]

STAGE_DEADLINES_HOURS = {
    "draft_generated":  48,
    "officer_review":   72,
    "survey_scheduled": 96,
    "claim_initiated":  48,
}


def _next_stage(current: str) -> str:
    try:
        idx = STAGE_ORDER.index(current)
        return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else current
    except ValueError:
        return current


def auto_trigger_relief_pipeline(district: str, crop: str, risk_data: dict):
    """Called from /api/crop-risk when risk_percent > RISK_THRESHOLD."""
    risk_percent = risk_data.get("risk_percent", 0)
    if risk_percent < RISK_THRESHOLD:
        return

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Don't create duplicate active cases for same district+crop
        existing = (
            db.query(ReliefCase)
            .filter(
                ReliefCase.district == district,
                ReliefCase.crop == crop,
                ReliefCase.status == "active",
            )
            .first()
        )
        if existing:
            return

        audit_trail = json.dumps([
            {
                "event": "auto_triggered",
                "timestamp": now.isoformat(),
                "risk_percent": risk_percent,
                "triggered_by": "XGBoost model",
                "district": district,
                "crop": crop,
            }
        ])

        case = ReliefCase(
            district=district,
            crop=crop,
            risk_percent=risk_percent,
            triggered_by="auto",
            triggered_at=now,
            pipeline_stage="draft_generated",
            stage_deadline=now + timedelta(hours=48),
            assigned_officer=f"District Agriculture Officer — {district}",
            farmer_count_affected=0,
            pmfby_claim_initiated=False,
            audit_trail=audit_trail,
            status="active",
        )
        db.add(case)

        db.add(ProactiveAlert(
            district=district,
            crop=crop,
            alert_type="crop_risk_window",
            message=(
                f"HIGH RISK ALERT: {crop.title()} in {district} has "
                f"{risk_percent}% loss probability. Relief draft auto-generated — review required."
            ),
            priority="HIGH",
            auto_generated=True,
        ))

        db.add(AuditLog(
            action=(
                f"Relief pipeline triggered for {district}/{crop} "
                f"(risk={risk_percent}%) — stage: draft_generated"
            ),
            timestamp=now.isoformat(),
            officer_name="SYSTEM-RELIEF",
        ))

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def advance_pipeline_stage(case_id: int, action: str, officer_id: str, note: str = ""):
    """Move a relief case to the next stage or reject it."""
    db = SessionLocal()
    try:
        now  = datetime.now(timezone.utc)
        case = db.query(ReliefCase).filter(ReliefCase.id == case_id).first()
        if not case:
            return {"error": "Case not found"}

        trail = json.loads(case.audit_trail or "[]")

        if action == "reject":
            case.status = "rejected"
            trail.append({
                "event": "rejected",
                "timestamp": now.isoformat(),
                "officer": officer_id,
                "note": note,
                "stage": case.pipeline_stage,
            })
        elif action == "approve":
            next_stage = _next_stage(case.pipeline_stage)
            trail.append({
                "event": "stage_advanced",
                "timestamp": now.isoformat(),
                "officer": officer_id,
                "from_stage": case.pipeline_stage,
                "to_stage": next_stage,
                "note": note,
            })
            case.pipeline_stage = next_stage
            deadline_hours = STAGE_DEADLINES_HOURS.get(next_stage, 48)
            case.stage_deadline = now + timedelta(hours=deadline_hours)

            if next_stage == "claim_initiated":
                case.pmfby_claim_initiated = True
            if next_stage == "completed":
                case.status = "completed"

        case.audit_trail = json.dumps(trail)
        db.add(case)
        db.commit()
        return {"stage": case.pipeline_stage, "status": case.status}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def check_pipeline_deadlines():
    """Auto-advance overdue pipeline stages. Runs every 60 seconds."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        cases = (
            db.query(ReliefCase)
            .filter(
                ReliefCase.status == "active",
                ReliefCase.stage_deadline.isnot(None),
            )
            .all()
        )

        for case in cases:
            deadline = case.stage_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if now <= deadline:
                continue

            next_stage = _next_stage(case.pipeline_stage)
            if next_stage == case.pipeline_stage:
                continue

            trail = json.loads(case.audit_trail or "[]")
            trail.append({
                "event": "auto_advanced_deadline_breach",
                "timestamp": now.isoformat(),
                "from_stage": case.pipeline_stage,
                "to_stage": next_stage,
            })
            case.pipeline_stage = next_stage
            case.audit_trail = json.dumps(trail)
            deadline_hours = STAGE_DEADLINES_HOURS.get(next_stage, 48)
            case.stage_deadline = now + timedelta(hours=deadline_hours)

            if next_stage == "completed":
                case.status = "completed"

            db.add(AuditLog(
                action=(
                    f"Relief case #{case.id} auto-advanced to '{next_stage}' "
                    f"(deadline breach)"
                ),
                timestamp=now.isoformat(),
                officer_name="SYSTEM-PIPELINE",
            ))

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
