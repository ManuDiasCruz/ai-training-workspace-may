"""Shared test fixtures.

The suite runs against a throwaway database built from the real CSV by the
real importer. Nothing is stubbed, so a test failure means the importer, the
schema or the API is genuinely broken -- and the developer's own
data/shopping.db is never touched.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config
from scripts.import_dataset import import_dataset

CSV_PATH = config.PROJECT_ROOT / "data" / "Shopping_data.csv"


@pytest.fixture(scope="session")
def csv_rows() -> list[dict[str, str]]:
    """The source CSV, parsed independently of the application code.

    Expected values are derived from this rather than from the API, so the
    tests compare the API against the dataset instead of against itself.
    """
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="session")
def test_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    db_file = tmp_path_factory.mktemp("shopapi") / "test_shopping.db"
    report = import_dataset(CSV_PATH, db_file)
    assert report.rows_imported == 200, "fixture database did not load the full dataset"
    return db_file


@pytest.fixture
def client(test_db: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """A client bound to the throwaway database.

    config.db_path() reads the environment on every call, so setting the
    variable here redirects the app without rebuilding it.
    """
    monkeypatch.setenv("SHOPAPI_DB_PATH", str(test_db))
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
