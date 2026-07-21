from sqlalchemy import Column, Integer, String
from database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    district = Column(String)
    aadhaar = Column(String)
    land_size = Column(String)
    crop_type = Column(String)
    income = Column(String)