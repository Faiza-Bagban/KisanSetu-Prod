"""
AUTOMATION 2 — Systemic Issue Detector
Runs every 5 minutes via APScheduler.
Flags districts where 5+ farmers file the same category within 7 days.
"""
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from database import SessionLocal
from models.grievance_model import Grievance
from models.systemic_issue_model import SystemicIssue
from models.audit_model import AuditLog


SYSTEMIC_THRESHOLD = 5
LOOKBACK_DAYS      = 7


def detect_systemic_issues():
    db = SessionLocal()
    try:
        now   = datetime.now(timezone.utc)
        since = now - timedelta(days=LOOKBACK_DAYS)

        recent = (
            db.query(Grievance)
            .filter(Grievance.created_at >= since)
            .all()
        )

        buckets = defaultdict(list)
        for g in recent:
            if g.jurisdiction and g.category:
                key = (g.jurisdiction, g.category)
                buckets[key].append(g.id)

        for (district, category), ids in buckets.items():
            if len(ids) < SYSTEMIC_THRESHOLD:
                continue

            # Check if we already created a systemic issue for this
            # district+category combination this week
            week_start = now - timedelta(days=7)
            exists = (
                db.query(SystemicIssue)
                .filter(
                    SystemicIssue.district == district,
                    SystemicIssue.category == category,
                    SystemicIssue.detected_at >= week_start,
                    SystemicIssue.status != "resolved",
                )
                .first()
            )
            if exists:
                # Update the count
                exists.farmer_count = len(ids)
                exists.individual_grievance_ids = json.dumps(ids)
                db.add(exists)
                continue

            issue = SystemicIssue(
                district=district,
                category=category,
                farmer_count=len(ids),
                individual_grievance_ids=json.dumps(ids),
                status="open",
                detected_at=now,
            )
            db.add(issue)
            db.add(AuditLog(
                action=(
                    f"SYSTEMIC ISSUE detected: {len(ids)} farmers in {district} "
                    f"filed '{category}' in 7 days. IDs: {ids}"
                ),
                timestamp=now.isoformat(),
                officer_name="SYSTEM-DETECTOR",
            ))

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
