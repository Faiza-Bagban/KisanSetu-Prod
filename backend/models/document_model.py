from sqlalchemy import Column, Integer, String
from database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer)
    document_type = Column(String)
    extracted_text = Column(String)
    verification_status = Column(String)