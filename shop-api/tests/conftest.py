"""Shared fixtures: build a throwaway database from the real CSV once per session."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.import_data import import_csv  # noqa: E402

CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"


@pytest.fixture(scope="session")
def client(tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest) -> TestClient:
    db_path = tmp_path_factory.mktemp("db") / "test_shop.db"
    import_csv(CSV_PATH, db_path)

    mp = pytest.MonkeyPatch()
    mp.setenv("SHOP_API_DB", str(db_path))
    request.addfinalizer(mp.undo)

    from app.main import app

    return TestClient(app)
