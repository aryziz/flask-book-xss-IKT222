# users.py
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal
from .models.user import User
from .security import hash_password, verify_password
from .utils.time import utc_now

import datetime

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 3

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
    now = utc_now()
    with SessionLocal() as s:
        u: User | None = s.execute(select(User).filter_by(email=email)).scalar_one_or_none()
        
        if not u:
            return None
        
        
        if not verify_password(u.password_hash, password):
            new_failed = (u.failed_attempts or 0) + 1
            locked_until = (
                now + datetime.timedelta(minutes=LOCK_MINUTES) if new_failed >= MAX_FAILED_ATTEMPTS else None
            )
            s.execute(
                update(User)
                .where(User.id == u.id)
                .values(failed_attempts=new_failed,
                locked_until=locked_until if locked_until else u.locked_until,
                updated_at=now)
            )
            s.commit()
            return None
        s.execute(update(User).where(User.id == u.id).values(failed_attempts=0, locked_until=None, updated_at=now))
        s.commit()
        return User(id=u.id, email=u.email, password_hash=u.password_hash, is_active=u.is_active, created_at=u.created_at)

def get_user(user_id: int) -> Optional[User]:
    with SessionLocal() as s:
        u = s.get(User, user_id)
        if not u:
            return None
        return User(id=u.id, email=u.email, password_hash=u.password_hash, is_active=u.is_active)


def is_locked(user: User) -> bool:
    return bool(user.locked_until is not None and user.locked_until > utc_now())

def bump_failure(user: User) -> None:
    now = utc_now()
    with SessionLocal() as s:
        u = s.get(User, user.id)
        if not u:
            return
        new_failed = (u.failed_attempts or 0) + 1
        locked_until = (
            now + datetime.timedelta(minutes=LOCK_MINUTES) if new_failed >= MAX_FAILED_ATTEMPTS else None
        )
        u.failed_attempts = new_failed
        if locked_until:
            u.locked_until = locked_until
        u.updated_at = now
        s.commit()

def reset_fail_state(user: User) -> None:
    with SessionLocal() as s:
        u = s.get(User, user.id)
        if not u:
            return
        u.failed_attempts = 0
        u.locked_until = None
        u.updated_at = utc_now()
        s.commit()