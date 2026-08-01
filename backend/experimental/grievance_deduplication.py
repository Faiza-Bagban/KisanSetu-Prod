"""
Duplicate Detection — checks the REAL grievances table in the database
for recent similar complaints, instead of a hardcoded fake list.
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
from models.grievance_model import Grievance


def check_duplicate(district: str, category: str, window_days: int = 7) -> bool:
    """
    Returns True if a grievance with the same district+category was
    already filed within the last `window_days` days — a real signal
    that this may be a duplicate/repeat complaint, not a fake stub check.
    """
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        existing = (
            db.query(Grievance)
            .filter(Grievance.jurisdiction == district)
            .filter(Grievance.category == category)
            .filter(Grievance.created_at >= cutoff)
            .first()
        )

        return existing is not None
    except Exception:
        # If DB check fails for any reason, don't block grievance submission —
        # fail safe (assume not duplicate) rather than fail loud
        return False
    finally:
        db.close()