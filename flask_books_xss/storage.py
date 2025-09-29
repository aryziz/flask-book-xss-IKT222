from typing import List, Dict
from .db import SessionLocal, Listing
from sqlalchemy import select, desc
import os

def add_book(title: str, price: str, seller: str) -> None:
    with SessionLocal() as s:
        if os.getenv("DEBUG") == "1":
            print(f"Adding book: title={title}, price={price}, seller={seller}")
        s.add(Listing(title=title, price=price, seller=seller))
        s.commit()

def list_books() -> List[Dict[str, str]]:
    with SessionLocal() as s:
        rows = s.execute(select(Listing).order_by(desc(Listing.created_at))).scalars().all()
        return [{"title": r.title, "price": r.price, "seller": r.seller, "created_at": r.created_at.isoformat()} for r in rows]
