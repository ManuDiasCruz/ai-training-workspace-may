import os
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """TestClient wired to a throwaway database seeded from the real CSV."""
    db_path = tmp_path / "test_shopping.db"
    monkeypatch.setenv("SHOPAPI_DB", str(db_path))

    from app.import_data import import_csv

    imported, skipped = import_csv(BASE_DIR / "data" / "Shopping_data.csv", db_path)
    assert imported == 200 and skipped == 0

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
