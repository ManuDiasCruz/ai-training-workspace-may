"""API tests. Each test run imports the CSV into a throwaway database."""

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB = PROJECT_ROOT / "tests" / "test_shop.db"


@pytest.fixture(scope="session")
def client():
    TEST_DB.unlink(missing_ok=True)
    os.environ["SHOP_API_DB"] = str(TEST_DB)

    from fastapi.testclient import TestClient

    from app.main import app
    from scripts.import_data import DEFAULT_CSV, import_csv

    count = import_csv(DEFAULT_CSV)
    assert count == 200

    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "customers": 200}


def test_list_customers_default_pagination(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 200
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["pages"] == 10
    assert len(body["items"]) == 20
    assert body["items"][0]["customer_id"] == 1


def test_list_customers_second_page(client):
    resp = client.get("/customers", params={"page": 2, "page_size": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert [c["customer_id"] for c in body["items"]] == [6, 7, 8, 9, 10]
    assert body["pages"] == 40


def test_list_customers_filters(client):
    resp = client.get(
        "/customers",
        params={"genre": "Female", "min_age": 30, "max_age": 40, "min_income": 60},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] > 0
    for c in body["items"]:
        assert c["genre"] == "Female"
        assert 30 <= c["age"] <= 40
        assert c["annual_income"] >= 60


def test_list_customers_sorting(client):
    resp = client.get(
        "/customers", params={"sort_by": "annual_income", "order": "desc", "page_size": 3}
    )
    assert resp.status_code == 200
    incomes = [c["annual_income"] for c in resp.json()["items"]]
    assert incomes == sorted(incomes, reverse=True)
    assert incomes[0] == 137


def test_list_customers_invalid_params(client):
    assert client.get("/customers", params={"page": 0}).status_code == 422
    assert client.get("/customers", params={"page_size": 101}).status_code == 422
    assert client.get("/customers", params={"genre": "Other"}).status_code == 422
    assert client.get("/customers", params={"sort_by": "nope"}).status_code == 422
    assert (
        client.get("/customers", params={"min_age": 50, "max_age": 20}).status_code == 422
    )


def test_get_customer_by_id(client):
    resp = client.get("/customers/1")
    assert resp.status_code == 200
    assert resp.json() == {
        "customer_id": 1,
        "genre": "Male",
        "age": 19,
        "annual_income": 15,
        "spending_score": 39,
    }


def test_get_customer_not_found(client):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_get_customer_invalid_id(client):
    assert client.get("/customers/abc").status_code == 422


def test_search_by_genre(client):
    resp = client.get("/customers/search", params={"q": "male"})
    assert resp.status_code == 200
    # LIKE '%male%' matches both 'Male' and 'Female' case-insensitively
    assert resp.json()["total"] == 200

    resp = client.get("/customers/search", params={"q": "fem"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 112
    assert all(c["genre"] == "Female" for c in body["items"])


def test_search_by_id(client):
    resp = client.get("/customers/search", params={"q": "0042"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["customer_id"] == 42


def test_search_requires_query(client):
    assert client.get("/customers/search").status_code == 422
    assert client.get("/customers/search", params={"q": ""}).status_code == 422


def test_stats(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_customers"] == 200
    assert body["avg_age"] == pytest.approx(38.85, abs=0.01)
    genres = {g["genre"]: g for g in body["by_genre"]}
    assert set(genres) == {"Male", "Female"}
    assert genres["Female"]["count"] == 112
    assert genres["Male"]["count"] == 88
