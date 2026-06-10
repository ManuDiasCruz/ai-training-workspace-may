"""Database engine, session factory and declarative base."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app import config

# SQLite requires check_same_thread=False so a connection can be used across
# FastAPI's worker threads; the argument is ignored for other backends.
_connect_args = (
    {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(config.DATABASE_URL, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
