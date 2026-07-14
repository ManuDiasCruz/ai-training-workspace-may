"""End-to-end API tests using an isolated temporary SQLite database."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.database import DEFAULT_DATASET_PATH
from app.main import create_app


@pytest.fixture
def client(tmp_path) -> Generator[TestClient, None, None]:
    application = create_app(tmp_path / "test-shopping.db", DEFAULT_DATASET_PATH)
    with TestClient(application) as test_client:
        yield test_client


def test_health_reports_imported_record_count(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "records": 200}


def test_list_supports_pagination_and_filters(client: TestClient) -> None:
    response = client.get(
        "/customers",
        params={
            "page": 2,
            "page_size": 5,
            "gender": "Female",
            "age_min": 25,
            "age_max": 35,
            "score_min": 70,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 2
    assert body["page_size"] == 5
    assert body["total"] > 5
    assert len(body["items"]) == 5
    assert all(item["gender"] == "Female" for item in body["items"])
    assert all(25 <= item["age"] <= 35 for item in body["items"])
    assert all(item["spending_score"] >= 70 for item in body["items"])


def test_search_and_customer_lookup(client: TestClient) -> None:
    search_response = client.get("/customers", params={"search": "0001"})
    customer_response = client.get("/customers/0001")

    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1
    assert search_response.json()["items"][0]["customer_id"] == "0001"
    assert customer_response.status_code == 200
    assert customer_response.json()["annual_income_kusd"] == 15


def test_invalid_range_and_missing_customer_are_handled(client: TestClient) -> None:
    invalid = client.get("/customers", params={"age_min": 50, "age_max": 20})
    blank_search = client.get("/customers", params={"search": "   "})
    missing = client.get("/customers/9999")

    assert invalid.status_code == 422
    assert invalid.json()["detail"] == "age_min cannot be greater than age_max"
    assert blank_search.status_code == 422
    assert "non-whitespace" in blank_search.json()["detail"]
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Customer not found"}
