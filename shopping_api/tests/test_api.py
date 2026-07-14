from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from shopping_api.app.main import app
from shopping_api.scripts.import_data import DEFAULT_SOURCE, import_dataset


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    database_path = tmp_path / "shopping.db"
    imported_rows = import_dataset(DEFAULT_SOURCE, database_path)
    assert imported_rows == 200
    monkeypatch.setenv("SHOPPING_DB_PATH", str(database_path))

    with TestClient(app) as test_client:
        yield test_client


def test_customer_list_is_stably_paginated(client: TestClient) -> None:
    response = client.get("/api/v1/customers", params={"page": 2, "page_size": 5})

    assert response.status_code == 200
    payload = response.json()
    assert [customer["customer_id"] for customer in payload["items"]] == [
        "0006",
        "0007",
        "0008",
        "0009",
        "0010",
    ]
    assert payload["pagination"] == {
        "page": 2,
        "page_size": 5,
        "total": 200,
        "total_pages": 40,
        "has_previous": True,
        "has_next": True,
    }


def test_filters_and_search_can_be_combined(client: TestClient) -> None:
    filtered = client.get(
        "/api/v1/customers",
        params={"gender": "Female", "income_min": 100, "score_min": 80},
    )
    searched = client.get("/api/v1/customers", params={"q": "0199"})

    assert filtered.status_code == 200
    assert [item["customer_id"] for item in filtered.json()["items"]] == [
        "0190",
        "0194",
    ]
    assert searched.status_code == 200
    assert searched.json()["items"] == [
        {
            "customer_id": "0199",
            "gender": "Male",
            "age": 32,
            "annual_income_kusd": 137,
            "spending_score": 18,
        }
    ]


def test_customer_lookup_and_client_errors(client: TestClient) -> None:
    found = client.get("/api/v1/customers/0001")
    missing = client.get("/api/v1/customers/9999")
    reversed_range = client.get(
        "/api/v1/customers", params={"age_min": 40, "age_max": 30}
    )
    blank_search = client.get("/api/v1/customers", params={"q": "   "})

    assert found.status_code == 200
    assert found.json()["customer_id"] == "0001"
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Customer not found."}
    assert reversed_range.status_code == 422
    assert reversed_range.json() == {
        "detail": "age_min cannot be greater than age_max."
    }
    assert blank_search.status_code == 422
    assert blank_search.json() == {"detail": "q cannot be blank."}


def test_missing_database_returns_actionable_503(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SHOPPING_DB_PATH", str(tmp_path / "missing.db"))

    with TestClient(app) as test_client:
        response = test_client.get("/health")

    assert response.status_code == 503
    assert "import_data" in response.json()["detail"]
