from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base


class Grievance(Base):
    __tablename__ = "grievances"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String, nullable=True, index=True)
    text = Column(String, nullable=True)
    translated_text = Column(String, nullable=True)
    category = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    resolution_days = Column(Integer, nullable=True)
    routed_officer = Column(String, nullable=True)
    status = Column(String, default="Under Review", nullable=True)
    jurisdiction = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ── AUTOMATION 1: SLA & ESCALATION ─────────────────────────
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    escalation_level = Column(Integer, default=0, nullable=True)   # 0=field 1=district 2=state
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_reason = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
