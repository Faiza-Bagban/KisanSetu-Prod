"""
AUTOMATION 5 — Officer Performance Scorecard
Computes scores per district officer from DB grievances.
Runs daily at midnight via APScheduler + on-demand via POST /api/officer-scores/refresh.
"""
from datetime import datetime, timezone
from database import SessionLocal
from models.grievance_model import Grievance
from models.officer_score_model import OfficerScore
from models.user_model import User


def _grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    return "D"


def compute_officer_scores():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        officers = (
            db.query(User)
            .filter(User.role.in_(["field_officer", "district_officer"]))
            .all()
        )

        for officer in officers:
            grievances = (
                db.query(Grievance)
                .filter(Grievance.jurisdiction == officer.district)
                .all()
            )
            total = len(grievances)
            if total == 0:
                score = 0.0
                resolved = escalated = sla_ok = 0
                avg_days = 0.0
            else:
                resolved  = sum(1 for g in grievances if g.status == "Resolved")
                escalated = sum(1 for g in grievances if (g.escalation_level or 0) > 0)
                sla_ok    = sum(
                    1 for g in grievances
                    if g.status == "Resolved"
                    and g.resolved_at is not None
                    and g.sla_deadline is not None
                    and g.resolved_at <= g.sla_deadline
                )
                days_list = [
                    g.resolution_days for g in grievances
                    if g.resolution_days is not None
                ]
                avg_days = sum(days_list) / len(days_list) if days_list else 0.0

                resolution_rate  = (resolved / total) * 100
                avg_days_score   = max(0, 100 - avg_days * 5)   # 0 days = 100, 20 days = 0
                escalation_rate  = (escalated / total) * 100
                sla_compliance   = (sla_ok / total) * 100

                score = (
                    resolution_rate  * 0.40
                    + avg_days_score * 0.30
                    + (100 - escalation_rate) * 0.20
                    + sla_compliance * 0.10
                )
                score = round(min(100, max(0, score)), 1)

            existing = (
                db.query(OfficerScore)
                .filter(OfficerScore.officer_id == officer.username)
                .first()
            )
            if existing:
                existing.total_grievances  = total
                existing.resolved_count    = resolved
                existing.avg_days          = round(avg_days, 1)
                existing.escalation_count  = escalated
                existing.sla_compliant_count = sla_ok
                existing.score             = score
                existing.grade             = _grade(score)
                existing.computed_at       = now
                db.add(existing)
            else:
                db.add(OfficerScore(
                    officer_id   = officer.username,
                    officer_name = officer.username.split("@")[0].replace(".", " ").title(),
                    district     = officer.district,
                    total_grievances    = total,
                    resolved_count      = resolved,
                    avg_days            = round(avg_days, 1),
                    escalation_count    = escalated,
                    sla_compliant_count = sla_ok,
                    score  = score,
                    grade  = _grade(score),
                    computed_at = now,
                ))

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
