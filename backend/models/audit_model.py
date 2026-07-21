from sqlalchemy import Column, Integer, String
from database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    timestamp = Column(String)
    officer_name = Column(String)