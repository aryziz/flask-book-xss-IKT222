from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

DB_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")

if DB_URL.startswith("sqlite:///"):
    Path("instance").mkdir(parents=True, exist_ok=True)
    
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))
Base = declarative_base()

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    seller = Column(String(100), nullable=False)
    price = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
def init_db():
    Base.metadata.create_all(bind=engine)