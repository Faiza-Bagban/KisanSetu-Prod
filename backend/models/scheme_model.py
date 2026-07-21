from sqlalchemy import Column, Integer, String
from database import Base

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    scheme_name = Column(String)
    eligibility_criteria = Column(String)
    required_documents = Column(String)
    benefit_amount = Column(String)