"""Pytest fixtures.

Environment variables are set *before* any ``app`` import so the SQLAlchemy
engine (built at import time) points at an isolated, throwaway SQLite file and
never touches the developer's real ``shopping.db``.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP_DIR = tempfile.mkdtemp(prefix="shopping_api_test_")
os.environ["SHOPPING_DB_PATH"] = str(Path(_TMP_DIR) / "test.db")
os.environ["SHOPPING_AUTO_SEED"] = "0"  # tests seed the DB explicitly


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.config import CSV_PATH
    from app.database import SessionLocal, init_db
    from app.importer import import_csv
    from app.main import app

    init_db()
    db = SessionLocal()
    try:
        import_csv(db, CSV_PATH, replace=True)
    finally:
        db.close()

    # ``with`` runs the app lifespan (startup/shutdown) around the tests.
    with TestClient(app) as test_client:
        yield test_client
