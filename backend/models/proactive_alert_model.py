from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from database import Base


class ProactiveAlert(Base):
    __tablename__ = "proactive_alerts"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String, nullable=True, index=True)
    crop = Column(String, nullable=True)
    alert_type = Column(String, nullable=True)
    message = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    is_read = Column(Boolean, default=False, nullable=True)
    auto_generated = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())