from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, func
from database import Base


class ReliefCase(Base):
    __tablename__ = "relief_cases"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String, nullable=True, index=True)
    crop = Column(String, nullable=True)
    risk_percent = Column(Float, nullable=True)
    triggered_by = Column(String, nullable=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    pipeline_stage = Column(String, default="draft_generated", nullable=True)
    stage_deadline = Column(DateTime(timezone=True), nullable=True)
    assigned_officer = Column(String, nullable=True)
    farmer_count_affected = Column(Integer, default=0, nullable=True)
    pmfby_claim_initiated = Column(Boolean, default=False, nullable=True)
    audit_trail = Column(String, nullable=True)  # JSON-encoded list
    status = Column(String, default="active", nullable=True)