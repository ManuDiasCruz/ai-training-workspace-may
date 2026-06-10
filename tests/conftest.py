"""Pytest fixtures.

A temporary, isolated SQLite database is configured *before* the application is
imported, so ``app.config`` reads these values at import time. The database is
seeded once per test session from the bundled dataset.
"""
from __future__ import annotations

import os
import tempfile

import pytest

# Configure an isolated temp DB and disable auto-seeding BEFORE importing app.
_DB_FD, _DB_PATH = tempfile.mkstemp(prefix="shopping_test_", suffix=".db")
os.environ["SHOPPING_DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ["SHOPPING_AUTO_SEED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app import config, models  # noqa: E402,F401  (models import registers tables)
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_database  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    """Create the schema and seed it from the bundled CSV for the test session."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session, config.DATASET_PATH)
    yield
    Base.metadata.drop_all(bind=engine)
    os.close(_DB_FD)
    if os.path.exists(_DB_PATH):
        os.remove(_DB_PATH)


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
