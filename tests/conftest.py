"""Shared fixtures: a throwaway database built from the real CSV dataset."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.import_data import import_csv

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "Shopping_data.csv"


@pytest.fixture(scope="session")
def csv_rows() -> list[dict]:
    """The source dataset as parsed dicts, for cross-checking API results."""
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as handle:
        return [
            {
                "customer_id": int(row["CustomerID"]),
                "genre": row["Genre"],
                "age": int(row["Age"]),
                "annual_income_k": int(row["Annual Income (k$)"]),
                "spending_score": int(row["Spending Score (1-100)"]),
            }
            for row in csv.DictReader(handle)
        ]


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory) -> Path:
    """Run the real import pipeline once into a temp database."""
    db_path = tmp_path_factory.mktemp("db") / "shopping_test.db"
    imported = import_csv(CSV_PATH, db_path)
    assert imported == 200
    return db_path


@pytest.fixture()
def client(test_db_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("SHOPPING_DB_PATH", str(test_db_path))
    return TestClient(app)
