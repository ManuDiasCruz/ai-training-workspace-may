"""Automated API tests.

A throwaway SQLite database is built in a temp directory and seeded from a
small in-memory CSV, so the tests never touch the real ``shopping.db``.
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point the app at an isolated database BEFORE importing app modules.
_TMP_DIR = tempfile.mkdtemp(prefix="shopping_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR) / 'test.db'}"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from scripts.import_data import import_data  # noqa: E402

SAMPLE_CSV = """CustomerID,Genre,Age,Annual Income (k$),Spending Score (1-100)
0001,Male,19,15,39
0002,Male,21,15,81
0003,Female,20,16,6
0004,Female,23,16,77
0005,Female,31,17,40
"""


@pytest.fixture(scope="module")
def client():
    csv_path = Path(_TMP_DIR) / "sample.csv"
    csv_path.write_text(SAMPLE_CSV, encoding="utf-8")
    Base.metadata.create_all(bind=engine)
    import_data(csv_path)
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_all(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["count"] == 5
    assert body["items"][0]["customer_id"] == 1


def test_pagination(client):
    resp = client.get("/customers", params={"limit": 2, "offset": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["count"] == 2
    assert [i["customer_id"] for i in body["items"]] == [3, 4]


def test_filter_by_genre(client):
    resp = client.get("/customers", params={"genre": "female"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert all(i["genre"] == "Female" for i in body["items"])


def test_filter_by_income_range(client):
    resp = client.get("/customers", params={"min_income": 16, "max_income": 16})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_search(client):
    resp = client.get("/customers", params={"search": "male"})
    assert resp.status_code == 200
    # "male" is a substring of "female", so it matches every record.
    assert resp.json()["total"] == 5


def test_get_one(client):
    resp = client.get("/customers/2")
    assert resp.status_code == 200
    assert resp.json()["spending_score"] == 81


def test_get_one_not_found(client):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404


def test_invalid_genre_rejected(client):
    resp = client.get("/customers", params={"genre": "other"})
    assert resp.status_code == 422


def test_invalid_age_range_rejected(client):
    resp = client.get("/customers", params={"min_age": 50, "max_age": 10})
    assert resp.status_code == 422


def test_stats(client):
    resp = client.get("/customers/stats/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_customers"] == 5
    assert body["male_count"] == 2
    assert body["female_count"] == 3
    assert body["min_annual_income_k"] == 15
    assert body["max_annual_income_k"] == 17
