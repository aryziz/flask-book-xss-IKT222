from __future__ import annotations
from sqlalchemy import (Column, DateTime, Integer, String, ForeignKey, Index, text, Text)
from sqlalchemy.orm import relationship
from .base import Base
from ..utils.time import utc_now

class Listing(Base):
    __tablename__ = "listing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    user = relationship("User", back_populates="listings")
Index("ix_listing_user_created_desc", Listing.user_id, text("created_at DESC"))