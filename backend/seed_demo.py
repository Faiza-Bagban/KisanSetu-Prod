"""
Demo seeder — called on startup if proactive_alerts table is empty.
Creates realistic data to showcase all 5 automations immediately.
"""
import json
from datetime import datetime, timezone, timedelta
from database import SessionLocal
from models.grievance_model import Grievance
from models.proactive_alert_model import ProactiveAlert
from models.relief_case_model import ReliefCase
from models.officer_score_model import OfficerScore
from models.audit_model import AuditLog


def seed_demo_data():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # ── 1. SLA-BREACHED GRIEVANCES (for Automation 1 demo) ─────────
        # These were created 5 days ago so escalation runs immediately
        old = now - timedelta(days=5)
        breached_grievances = [
            Grievance(
                farmer_id="farmer1@demo.in",
                text="PM-KISAN payment not received for last 3 installments",
                category="payment_issue",
                confidence=91.2,
                resolution_days=10,
                routed_officer="District Finance Officer",
                status="Under Review",
                jurisdiction="Nashik",
                created_at=old,
                updated_at=old,
                sla_deadline=old + timedelta(days=3),   # deadline was 2 days ago
                escalation_level=0,
            ),
            Grievance(
                farmer_id="farmer2@demo.in",
                text="Crop insurance claim rejected without valid reason",
                category="document_rejection",
                confidence=87.5,
                resolution_days=4,
                routed_officer="District Agriculture Officer",
                status="Under Review",
                jurisdiction="Pune",
                created_at=old,
                updated_at=old,
                sla_deadline=old + timedelta(days=3),
                escalation_level=0,
            ),
            Grievance(
                farmer_id="farmer3@demo.in",
                text="Officer demanded bribe for scheme approval",
                category="officer_misconduct",
                confidence=93.0,
                resolution_days=18,
                routed_officer="Vigilance Officer",
                status="Under Review",
                jurisdiction="Aurangabad",
                created_at=old,
                updated_at=old,
                sla_deadline=old + timedelta(days=3),
                escalation_level=0,
            ),
        ]
        db.add_all(breached_grievances)

        # ── 2. SYSTEMIC ISSUE SEED — 6 Nashik payment_issue in 3 days ──
        recent = now - timedelta(days=3)
        systemic_grievances = [
            Grievance(
                farmer_id=f"nashik_farmer{i}@demo.in",
                text=f"PM-KISAN payment not received — farmer {i} from Nashik",
                category="payment_issue",
                confidence=88.0 + i,
                resolution_days=10,
                routed_officer="District Finance Officer",
                status="Under Review",
                jurisdiction="Nashik",
                created_at=recent,
                updated_at=recent,
                sla_deadline=recent + timedelta(days=3),
                escalation_level=0,
            )
            for i in range(1, 7)
        ]
        db.add_all(systemic_grievances)
        db.flush()  # get IDs

        systemic_ids = [g.id for g in systemic_grievances]

        # ── 3. RELIEF CASE — Nashik at officer_review stage ─────────────
        relief_trail = json.dumps([
            {
                "event": "auto_triggered",
                "timestamp": (now - timedelta(hours=30)).isoformat(),
                "risk_percent": 82.0,
                "triggered_by": "XGBoost model",
                "district": "Nashik",
                "crop": "soybean",
            },
            {
                "event": "stage_advanced",
                "timestamp": (now - timedelta(hours=20)).isoformat(),
                "officer": "SYSTEM",
                "from_stage": "draft_generated",
                "to_stage": "officer_review",
                "note": "Auto-advanced after draft generation",
            },
        ])
        db.add(ReliefCase(
            district="Nashik",
            crop="soybean",
            risk_percent=82.0,
            triggered_by="auto",
            triggered_at=now - timedelta(hours=30),
            pipeline_stage="officer_review",
            stage_deadline=now + timedelta(hours=18),
            assigned_officer="District Agriculture Officer — Nashik",
            farmer_count_affected=6,
            pmfby_claim_initiated=False,
            audit_trail=relief_trail,
            status="active",
        ))

        # ── 4. SEASONAL ALERTS (pre_kharif_prep = May 2026) ─────────────
        alert_templates = [
            {
                "district": "Nashik",
                "alert_type": "crop_risk_window",
                "message": "Pre-Kharif preparation window open. Ensure soil moisture assessments are filed before June sowing.",
                "priority": "HIGH",
            },
            {
                "district": "Pune",
                "alert_type": "scheme_deadline",
                "message": "PM-KISAN 18th installment registration closes June 1. Verify beneficiary lists now.",
                "priority": "HIGH",
            },
            {
                "district": "Aurangabad",
                "alert_type": "document_renewal",
                "message": "PMFBY Kharif crop insurance enrolment deadline approaching. Prompt farmers to submit declarations.",
                "priority": "MEDIUM",
            },
            {
                "district": "Kolhapur",
                "alert_type": "survey_reminder",
                "message": "Field survey for Kharif crop area estimation must begin by May 25. Assign field officers.",
                "priority": "MEDIUM",
            },
            {
                "district": "Nagpur",
                "alert_type": "scheme_deadline",
                "message": "PMFBY premium subsidy disbursement requires district officer sign-off by May 31.",
                "priority": "HIGH",
            },
            {
                "district": "Solapur",
                "alert_type": "crop_risk_window",
                "message": "Low soil moisture detected in Solapur. Recommend early Kharif advisory distribution.",
                "priority": "MEDIUM",
            },
        ]
        for a in alert_templates:
            db.add(ProactiveAlert(
                district=a["district"],
                crop="pre_kharif_prep",
                alert_type=a["alert_type"],
                message=a["message"],
                priority=a["priority"],
                valid_until=now + timedelta(days=30),
                is_read=False,
                auto_generated=True,
            ))

        # ── 5. OFFICER SCORES (realistic variance for scoreboard) ────────
        demo_scores = [
            {"officer_id": "nashik.officer@kisansetu.gov",    "district": "Nashik",     "name": "Raj Patil",      "score": 88.0, "grade": "A", "total": 14, "resolved": 12, "esc": 1},
            {"officer_id": "pune.officer@kisansetu.gov",      "district": "Pune",       "name": "Meera Shah",     "score": 67.0, "grade": "B", "total": 21, "resolved": 14, "esc": 4},
            {"officer_id": "aurangabad.officer@kisansetu.gov","district": "Aurangabad", "name": "Suresh Kumar",   "score": 45.0, "grade": "C", "total": 28, "resolved": 12, "esc": 9},
            {"officer_id": "kolhapur.officer@kisansetu.gov",  "district": "Kolhapur",   "name": "Priya Deshmukh", "score": 75.0, "grade": "B", "total": 11, "resolved": 8,  "esc": 2},
            {"officer_id": "nagpur.officer@kisansetu.gov",    "district": "Nagpur",     "name": "Amit Wagh",      "score": 92.0, "grade": "A", "total": 9,  "resolved": 9,  "esc": 0},
            {"officer_id": "solapur.officer@kisansetu.gov",   "district": "Solapur",    "name": "Sneha Jadhav",   "score": 38.0, "grade": "D", "total": 17, "resolved": 6,  "esc": 7},
        ]
        for s in demo_scores:
            existing = db.query(OfficerScore).filter(OfficerScore.officer_id == s["officer_id"]).first()
            if not existing:
                db.add(OfficerScore(
                    officer_id=s["officer_id"],
                    officer_name=s["name"],
                    district=s["district"],
                    total_grievances=s["total"],
                    resolved_count=s["resolved"],
                    avg_days=7.0,
                    escalation_count=s["esc"],
                    sla_compliant_count=s["resolved"] - 1,
                    score=s["score"],
                    grade=s["grade"],
                    computed_at=now,
                ))

        # ── 6. AUDIT LOG ENTRIES ─────────────────────────────────────────
        db.add(AuditLog(
            action="Demo data seeded — SLA-breached grievances, systemic cluster, relief case, seasonal alerts, officer scores",
            timestamp=now.isoformat(),
            officer_name="SYSTEM-SEED",
        ))

        db.commit()
        print("[SEED] Demo data seeded successfully")

    except Exception as e:
        db.rollback()
        print(f"[SEED] Error: {e}")
    finally:
        db.close()


def maybe_seed():
    """Call on startup — seeds only if proactive_alerts table is empty."""
    db = SessionLocal()
    try:
        count = db.query(ProactiveAlert).count()
        if count == 0:
            seed_demo_data()
    finally:
        db.close()
