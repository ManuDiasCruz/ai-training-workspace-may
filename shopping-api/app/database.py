"""Database engine and session configuration.

Uses SQLite for a zero-dependency, fully local setup. The database file
location can be overridden with the ``SHOPPING_DB_PATH`` environment variable,
which the test suite uses to run against an isolated database.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default DB lives next to the data file, at the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "shopping.db"

DB_PATH = os.getenv("SHOPPING_DB_PATH", str(DEFAULT_DB_PATH))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False is required for SQLite under FastAPI's threadpool.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a scoped session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
