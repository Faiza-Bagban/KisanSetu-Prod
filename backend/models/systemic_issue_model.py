from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base


class SystemicIssue(Base):
    __tablename__ = "systemic_issues"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True)
    farmer_count = Column(Integer, default=0, nullable=True)
    individual_grievance_ids = Column(String, nullable=True)  # JSON-encoded list
    status = Column(String, default="open", nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())