from __future__ import annotations
from sqlalchemy import (Column, DateTime, Integer, String, text)
from sqlalchemy.orm import relationship
from .base import Base
from ..utils.time import utc_now

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Integer, nullable=False, server_default=text("1"))
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    
    listings = relationship("Listing", back_populates="user", cascade="all, delete-orphan")