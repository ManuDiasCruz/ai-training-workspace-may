"""Database engine, session factory and declarative base.

A single local SQLite file (``shopping.db``) backs the whole application. The
location can be overridden with the ``DATABASE_URL`` environment variable, which
is mainly used by the test suite to point at an isolated database.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Default to a SQLite file living next to the project root.
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "shopping.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")

# ``check_same_thread`` only matters for SQLite; it lets the connection be
# shared across the threads FastAPI/uvicorn use to serve requests.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


def get_db():
    """FastAPI dependency that yields a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
