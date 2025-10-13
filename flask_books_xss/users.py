# users.py
from typing import Optional
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal
from .models.user import User
from .security import hash_password, verify_password
from flask import current_app

def create_user(email: str, password: str) -> User:
    email = email.strip().lower()
    with SessionLocal() as s:
        u = User(email=email, password_hash=hash_password(password))
        s.add(u)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            raise ValueError("email_already_registered")
        s.refresh(u)
        return u

def authenticate(email: str, password: str) -> Optional[User]:
    email = email.strip().lower()
    with SessionLocal() as s:
        u = s.query(User).filter_by(email=email).first()
        if current_app.config.get("DEBUG"):
            print(f"Authenticating user: email={email}, found={'yes' if u else 'no'}")
        if not u:
            return None
        return u if verify_password(u.password_hash, password) else None

def get_user(user_id: int) -> Optional[User]:
    with SessionLocal() as s:
        return s.get(User, user_id)
