#backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:kolhe%40123@localhost:5432/kisansetu"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency (used in FastAPI later)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()