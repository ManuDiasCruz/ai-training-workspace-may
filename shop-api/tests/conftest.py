"""Shared fixtures: a throwaway database built from the real CSV."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"

TOTAL_ROWS = 200


@pytest.fixture(scope="session")
def csv_rows() -> list[dict[str, str]]:
    """The raw dataset, used as an independent oracle for API responses."""
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="session")
def client(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    """A TestClient backed by a temporary database, never the developer's own."""
    from app.db import connect, init_schema
    from app.importer import import_csv

    db_path = tmp_path_factory.mktemp("shop-api-db") / "test.db"
    previous = os.environ.get("SHOP_API_DB_PATH")
    os.environ["SHOP_API_DB_PATH"] = str(db_path)

    conn = connect(db_path)
    try:
        init_schema(conn)
        report = import_csv(conn, CSV_PATH)
    finally:
        conn.close()
    assert report.rows_imported == TOTAL_ROWS, f"fixture import failed: {report.rejects}"

    from app.main import app

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous is None:
            os.environ.pop("SHOP_API_DB_PATH", None)
        else:
            os.environ["SHOP_API_DB_PATH"] = previous
