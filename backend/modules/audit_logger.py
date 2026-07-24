# backend/modules/audit_logger.py
# Week 3 Day 3 (Sakshi) — Centralized audit logging utility.
# Sensitive routes import log_event() to record security-relevant actions.
# Stores in memory (200-entry cap) + writes to audit_logs DB table.

from datetime import datetime, timezone
from sqlalchemy.orm import Session


# In-memory log (fast, for /api/audit-logs endpoint)
_audit_log: list[dict] = []
MAX_LOG_SIZE = 200


def log_event(
    action: str,
    user: str,
    role: str,
    detail: str = "",
    db: Session | None = None,
) -> None:
    """
    Record a security-relevant action.

    Args:
        action:  Short action name e.g. "IDP_EXTRACT", "GRIEVANCE_SUBMIT"
        user:    Username (JWT sub claim)
        role:    User role (JWT role claim)
        detail:  Optional extra context (filename, grievance id, etc.)
        db:      Optional SQLAlchemy session — if provided, also writes to DB
    """
    entry = {
        "action": action,
        "user": user,
        "role": role,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # In-memory store
    _audit_log.append(entry)
    if len(_audit_log) > MAX_LOG_SIZE:
        _audit_log.pop(0)

    # DB write (non-blocking — if it fails, don't crash the request)
    if db is not None:
        try:
            from models.audit_model import AuditLog
            db.add(AuditLog(
                action=action,
                timestamp=entry["timestamp"],
                officer_name=f"{user} ({role})",
            ))
            db.commit()
        except Exception:
            db.rollback()


def get_recent_logs(n: int = 20) -> list[dict]:
    """Return the last n audit entries from memory."""
    return _audit_log[-n:]