from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base


class OfficerScore(Base):
    __tablename__ = "officer_scores"

    id = Column(Integer, primary_key=True, index=True)
    officer_id = Column(String, nullable=True, index=True)
    officer_name = Column(String, nullable=True)
    district = Column(String, nullable=True)
    total_grievances = Column(Integer, default=0, nullable=True)
    resolved_count = Column(Integer, default=0, nullable=True)
    avg_days = Column(Float, default=0.0, nullable=True)
    escalation_count = Column(Integer, default=0, nullable=True)
    sla_compliant_count = Column(Integer, default=0, nullable=True)
    score = Column(Float, default=0.0, nullable=True)
    grade = Column(String, nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())