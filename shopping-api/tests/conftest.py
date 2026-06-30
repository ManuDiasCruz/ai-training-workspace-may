"""Pytest fixtures: build an isolated SQLite DB seeded from the dataset CSV."""
import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway database BEFORE importing app modules.
_TMP_DB = Path(tempfile.gettempdir()) / "shopping_test.db"
os.environ["SHOPPING_DB_PATH"] = str(_TMP_DB)

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from scripts.import_data import DEFAULT_CSV, load_rows  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seed_database():
    """Create a fresh schema and load the dataset once per test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.bulk_save_objects(list(load_rows(DEFAULT_CSV)))
        session.commit()
    finally:
        session.close()
    yield
    Base.metadata.drop_all(bind=engine)
    # Release the SQLite file handle before deleting (required on Windows).
    engine.dispose()
    try:
        _TMP_DB.unlink(missing_ok=True)
    except OSError:
        pass


@pytest.fixture()
def client():
    return TestClient(app)
