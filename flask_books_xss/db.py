from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import event, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DB_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")

if DB_URL.startswith("sqlite:///"):
    Path("instance").mkdir(parents=True, exist_ok=True)
    
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
                       pool_pre_ping=True)

if DB_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))