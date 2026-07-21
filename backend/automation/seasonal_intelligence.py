"""
AUTOMATION 3 — Seasonal Proactive Intelligence
Runs daily at 06:00 via APScheduler.
Generates context-aware alerts for every district based on Maharashtra crop calendar.
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
from models.proactive_alert_model import ProactiveAlert

DISTRICTS = ["Pune", "Nashik", "Nagpur", "Aurangabad", "Kolhapur", "Solapur"]

CROP_CALENDAR = {
    "kharif_sowing":   {"months": [6, 7],    "crops": ["rice", "soybean", "cotton"]},
    "kharif_harvest":  {"months": [10, 11],  "crops": ["rice", "soybean", "cotton"]},
    "rabi_sowing":     {"months": [11, 12],  "crops": ["wheat", "gram", "onion"]},
    "rabi_harvest":    {"months": [3, 4],    "crops": ["wheat", "gram", "onion"]},
    "pre_kharif_prep": {"months": [4, 5],    "crops": ["all"]},
}

# Alert templates keyed by season
ALERT_TEMPLATES = {
    "pre_kharif_prep": [
        {
            "alert_type": "crop_risk_window",
            "message": "Pre-Kharif preparation window open. Ensure soil moisture assessments are filed before June sowing season.",
            "priority": "HIGH",
        },
        {
            "alert_type": "scheme_deadline",
            "message": "PM-KISAN 18th installment registration closes June 1. Verify beneficiary lists now.",
            "priority": "HIGH",
        },
        {
            "alert_type": "document_renewal",
            "message": "PMFBY crop insurance enrolment deadline approaching. Prompt farmers to submit Kharif crop declarations.",
            "priority": "MEDIUM",
        },
        {
            "alert_type": "survey_reminder",
            "message": "Field survey for Kharif crop area estimation must begin by May 25. Assign field officers.",
            "priority": "MEDIUM",
        },
    ],
    "kharif_sowing": [
        {
            "alert_type": "crop_risk_window",
            "message": "Kharif sowing season active. Monitor rainfall and issue crop advisory for rice/soybean districts.",
            "priority": "HIGH",
        },
        {
            "alert_type": "scheme_deadline",
            "message": "PMFBY Kharif enrolment window closing. Ensure all farmers are registered.",
            "priority": "HIGH",
        },
    ],
    "kharif_harvest": [
        {
            "alert_type": "survey_reminder",
            "message": "Kharif crop cutting experiments due. Assign officers for yield estimation surveys.",
            "priority": "HIGH",
        },
        {
            "alert_type": "document_renewal",
            "message": "Post-harvest loss assessments must be filed within 7 days of harvest completion.",
            "priority": "MEDIUM",
        },
    ],
    "rabi_sowing": [
        {
            "alert_type": "scheme_deadline",
            "message": "Rabi PMFBY enrolment open. Ensure wheat and gram farmers are covered.",
            "priority": "HIGH",
        },
    ],
    "rabi_harvest": [
        {
            "alert_type": "survey_reminder",
            "message": "Rabi yield surveys must be completed before procurement begins.",
            "priority": "MEDIUM",
        },
    ],
}


def _current_season(month: int):
    for season, info in CROP_CALENDAR.items():
        if month in info["months"]:
            return season
    return None


def generate_seasonal_alerts():
    db = SessionLocal()
    try:
        now    = datetime.now(timezone.utc)
        season = _current_season(now.month)
        if not season:
            return

        templates = ALERT_TEMPLATES.get(season, [])
        valid_until = now + timedelta(days=30)

        for district in DISTRICTS:
            for tmpl in templates:
                # Avoid duplicating alerts for the same district+type this month
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                exists = (
                    db.query(ProactiveAlert)
                    .filter(
                        ProactiveAlert.district == district,
                        ProactiveAlert.alert_type == tmpl["alert_type"],
                        ProactiveAlert.created_at >= month_start,
                    )
                    .first()
                )
                if exists:
                    continue

                db.add(ProactiveAlert(
                    district=district,
                    crop=season,
                    alert_type=tmpl["alert_type"],
                    message=tmpl["message"],
                    priority=tmpl["priority"],
                    valid_until=valid_until,
                    is_read=False,
                    auto_generated=True,
                ))

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
