# listings.py
from typing import List, Dict, Optional
from sqlalchemy import select, desc
from .db import SessionLocal
from .models.listing import Listing

def create_listing(user_id: int, title: str, price: int, description: Optional[str] = None) -> Listing:
    if not isinstance(price, int):
        try:
            price = int(price)
        except Exception:
            raise ValueError("price_must_be_int")
    title = title.strip()
    with SessionLocal() as s:
        row = Listing(user_id=user_id, title=title, price=price, description=description)
        s.add(row)
        s.commit()
        s.refresh(row)
        return row

def list_public() -> List[Dict]:
    """All listings newest-first (no PII)."""
    with SessionLocal() as s:
        rows = s.execute(select(Listing).order_by(desc(Listing.created_at))).scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "price": r.price,
                "created_at": r.created_at.isoformat(),
                "user_id": r.user_id,
            }
            for r in rows
        ]

def list_mine(user_id: int) -> List[Dict]:
    """Only current user's listings, newest-first."""
    with SessionLocal() as s:
        rows = (
            s.execute(
                select(Listing)
                .where(Listing.user_id == user_id)
                .order_by(desc(Listing.created_at))
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "price": r.price,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]

def delete_listing(user_id: int, listing_id: int) -> bool:
    """Hard delete (SQLite). Enforce ownership."""
    with SessionLocal() as s:
        row = s.get(Listing, listing_id)
        if not row or row.user_id != user_id:
            return False
        s.delete(row)
        s.commit()
        return True

def update_listing(user_id: int, listing_id: int, *, title: Optional[str] = None, price: Optional[int] = None, description: Optional[str] = None) -> bool:
    with SessionLocal() as s:
        row = s.get(Listing, listing_id)
        if not row or row.user_id != user_id:
            return False
        if title is not None:
            row.title = title.strip()
        if price is not None:
            row.price = int(price)
        if description is not None:
            row.description = description
        s.commit()
        return True
