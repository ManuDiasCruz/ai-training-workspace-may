"""End-to-end API tests running against a temporary database built from the real CSV."""

import pytest
from fastapi.testclient import TestClient

from app.import_data import DEFAULT_CSV_PATH, import_csv
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Build a throwaway SQLite DB from the dataset and point the app at it."""
    db_path = tmp_path / "test_shopping.db"
    monkeypatch.setenv("SHOPPING_DB_PATH", str(db_path))
    count = import_csv(DEFAULT_CSV_PATH, db_path)
    assert count == 200
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_row_count(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "customers": 200}


def test_list_customers_default_pagination(client):
    response = client.get("/customers")
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 200
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total_pages"] == 10
    assert len(body["items"]) == 20
    assert body["items"][0] == {
        "customer_id": 1,
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }


def test_pagination_returns_distinct_pages(client):
    page1 = client.get("/customers", params={"page": 1, "page_size": 5}).json()
    page2 = client.get("/customers", params={"page": 2, "page_size": 5}).json()
    ids_page1 = [item["customer_id"] for item in page1["items"]]
    ids_page2 = [item["customer_id"] for item in page2["items"]]
    assert ids_page1 == [1, 2, 3, 4, 5]
    assert ids_page2 == [6, 7, 8, 9, 10]


def test_page_size_bounds_are_validated(client):
    assert client.get("/customers", params={"page_size": 0}).status_code == 422
    assert client.get("/customers", params={"page_size": 500}).status_code == 422
    assert client.get("/customers", params={"page": 0}).status_code == 422


def test_filter_by_genre_is_case_insensitive(client):
    response = client.get("/customers", params={"genre": "male", "page_size": 100})
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 88  # dataset has 88 male / 112 female customers
    assert all(item["genre"] == "Male" for item in body["items"])


def test_filter_rejects_unknown_genre(client):
    response = client.get("/customers", params={"genre": "robot"})
    assert response.status_code == 422
    assert "Invalid genre" in response.json()["detail"]


def test_filter_by_income_range(client):
    response = client.get(
        "/customers",
        params={"min_income": 120, "max_income": 137, "page_size": 100},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 6
    assert all(120 <= item["annual_income_k"] <= 137 for item in body["items"])


def test_inverted_range_is_rejected(client):
    response = client.get("/customers", params={"min_age": 60, "max_age": 20})
    assert response.status_code == 422
    assert "min_age" in response.json()["detail"]


def test_sorting_by_income_desc(client):
    response = client.get(
        "/customers", params={"sort_by": "annual_income_k", "order": "desc", "page_size": 2}
    )
    assert response.status_code == 200
    incomes = [item["annual_income_k"] for item in response.json()["items"]]
    assert incomes == [137, 137]


def test_get_customer_by_id(client):
    response = client.get("/customers/42")
    assert response.status_code == 200
    assert response.json() == {
        "customer_id": 42,
        "genre": "Male",
        "age": 24,
        "annual_income_k": 38,
        "spending_score": 92,
    }


def test_get_customer_not_found(client):
    response = client.get("/customers/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_search_by_genre_fragment(client):
    response = client.get("/customers/search", params={"q": "fem", "page_size": 100})
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 112
    assert all(item["genre"] == "Female" for item in body["items"])


def test_search_numeric_matches_any_numeric_field(client):
    response = client.get("/customers/search", params={"q": "137", "page_size": 100})
    assert response.status_code == 200
    ids = sorted(item["customer_id"] for item in response.json()["items"])
    # 137 matches customer_id 137 plus the two customers earning 137 k$.
    assert ids == [137, 199, 200]


def test_search_requires_query(client):
    assert client.get("/customers/search").status_code == 422


def test_stats_summary(client):
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_customers"] == 200
    assert body["min_annual_income_k"] == 15
    assert body["max_annual_income_k"] == 137
    assert body["avg_age"] == pytest.approx(38.85, abs=0.01)
    genres = {entry["genre"]: entry["customers"] for entry in body["by_genre"]}
    assert genres == {"Female": 112, "Male": 88}
