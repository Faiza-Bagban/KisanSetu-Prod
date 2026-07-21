"""
AUTOMATION 1 — Auto-Escalation Engine with SLA Timers
Runs every 60 seconds via APScheduler.
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
from models.grievance_model import Grievance
from models.audit_model import AuditLog

FIELD_OFFICER_SLA_DAYS    = 3
DISTRICT_OFFICER_SLA_DAYS = 2
STATE_DEPT_SLA_DAYS       = 2


def check_and_escalate_grievances():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        active = (
            db.query(Grievance)
            .filter(
                Grievance.status != "Resolved",
                Grievance.escalation_level < 2,
                Grievance.sla_deadline.isnot(None),
            )
            .all()
        )

        for g in active:
            deadline = g.sla_deadline
            if deadline is None:
                continue
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if now <= deadline:
                continue

            if g.escalation_level == 0:
                g.escalation_level = 1
                g.routed_officer = f"District Agriculture Officer — {g.jurisdiction or 'Pune'}"
                g.sla_deadline = now + timedelta(days=DISTRICT_OFFICER_SLA_DAYS)
                g.escalated_at = now
                g.escalation_reason = "Field officer SLA breach"
                reason = f"Grievance #{g.id} auto-escalated to District Officer (field SLA breach)"

            elif g.escalation_level == 1:
                g.escalation_level = 2
                g.routed_officer = "State Agriculture Department"
                g.sla_deadline = now + timedelta(days=STATE_DEPT_SLA_DAYS)
                g.escalated_at = now
                g.escalation_reason = "District officer SLA breach"
                reason = f"Grievance #{g.id} escalated to State Dept (district SLA breach)"

            db.add(AuditLog(
                action=reason,
                timestamp=now.isoformat(),
                officer_name="SYSTEM-ESCALATION",
            ))

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
