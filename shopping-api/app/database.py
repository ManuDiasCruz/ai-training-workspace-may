"""Database engine and session management for the Shopping API.

The SQLite database file location can be overridden with the
``SHOPPING_API_DB`` environment variable, which keeps tests and local
runs isolated from each other.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "shopping.db"


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    db_path = os.environ.get("SHOPPING_API_DB", str(DEFAULT_DB_PATH))
    return f"sqlite:///{db_path}"


engine = create_engine(_database_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    """FastAPI dependency that yields a database session."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
