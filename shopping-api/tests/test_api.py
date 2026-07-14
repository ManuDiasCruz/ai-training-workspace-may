"""API tests. A temporary SQLite database is seeded from the real CSV."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Point the app at a throwaway database BEFORE importing it.
_TEST_DB = PROJECT_ROOT / "tests" / "test_shopping.db"
os.environ["SHOPPING_API_DB"] = str(_TEST_DB)

import pytest
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app
from scripts.import_data import import_csv


@pytest.fixture(scope="session", autouse=True)
def seeded_database():
    if _TEST_DB.exists():
        _TEST_DB.unlink()
    imported, errors = import_csv(PROJECT_ROOT / "data" / "Shopping_data.csv")
    assert imported == 200
    assert errors == []
    yield
    # Release SQLite file handles before deleting (required on Windows).
    engine.dispose()
    if _TEST_DB.exists():
        _TEST_DB.unlink()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "customers": 200}


def test_list_customers_default_pagination(client):
    response = client.get("/customers")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 200
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["pages"] == 10
    assert len(body["items"]) == 20
    assert body["items"][0] == {
        "id": 1,
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }


def test_list_customers_second_page_no_overlap(client):
    first = client.get("/customers", params={"page": 1, "page_size": 5}).json()
    second = client.get("/customers", params={"page": 2, "page_size": 5}).json()
    first_ids = {c["id"] for c in first["items"]}
    second_ids = {c["id"] for c in second["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_filter_by_genre_and_ranges(client):
    response = client.get(
        "/customers",
        params={"genre": "Female", "min_age": 30, "max_age": 40, "min_income": 60},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    for customer in body["items"]:
        assert customer["genre"] == "Female"
        assert 30 <= customer["age"] <= 40
        assert customer["annual_income_k"] >= 60


def test_sorting_desc(client):
    response = client.get(
        "/customers", params={"sort_by": "annual_income_k", "order": "desc"}
    )
    incomes = [c["annual_income_k"] for c in response.json()["items"]]
    assert incomes == sorted(incomes, reverse=True)
    assert incomes[0] == 137


def test_invalid_range_returns_400(client):
    response = client.get("/customers", params={"min_age": 50, "max_age": 20})
    assert response.status_code == 400
    assert "Invalid range" in response.json()["detail"]


def test_invalid_query_type_returns_422(client):
    response = client.get("/customers", params={"page": "abc"})
    assert response.status_code == 422


def test_get_customer_by_id(client):
    response = client.get("/customers/200")
    assert response.status_code == 200
    assert response.json() == {
        "id": 200,
        "genre": "Male",
        "age": 30,
        "annual_income_k": 137,
        "spending_score": 83,
    }


def test_get_missing_customer_returns_404(client):
    response = client.get("/customers/9999")
    assert response.status_code == 404


def test_search_by_genre_text(client):
    response = client.get("/customers/search", params={"q": "female"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 112  # 112 female customers in the dataset
    assert all(c["genre"] == "Female" for c in body["items"])


def test_search_numeric_matches_multiple_fields(client):
    response = client.get("/customers/search", params={"q": "137"})
    assert response.status_code == 200
    body = response.json()
    ids = {c["id"] for c in body["items"]}
    assert {137, 199, 200}.issubset(ids)  # id 137 plus the two 137k incomes


def test_search_requires_term(client):
    response = client.get("/customers/search")
    assert response.status_code == 422


def test_stats(client):
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_customers"] == 200
    assert body["by_genre"]["Female"]["count"] == 112
    assert body["by_genre"]["Male"]["count"] == 88
    assert 0 < body["avg_spending_score"] <= 100
