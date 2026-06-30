"""End-to-end API tests against a temporary SQLite database."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from shopping_api.app import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOPPING_DB_PATH", str(tmp_path / "test-shopping.db"))
    with TestClient(app) as test_client:
        yield test_client


def test_lists_a_paginated_second_page(client: TestClient) -> None:
    response = client.get("/customers", params={"page": 2, "page_size": 25})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 200
    assert body["pages"] == 8
    assert len(body["items"]) == 25
    assert body["items"][0]["customer_id"] == "0026"


def test_combines_genre_and_age_filters(client: TestClient) -> None:
    response = client.get(
        "/customers",
        params={"genre": "Male", "age_min": 60, "age_max": 70, "page_size": 100},
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["genre"] == "Male" and 60 <= item["age"] <= 70 for item in items)


def test_searches_across_customer_fields(client: TestClient) -> None:
    response = client.get("/customers", params={"q": "0001"})

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "customer_id": "0001",
            "genre": "Male",
            "age": 19,
            "annual_income_k": 15,
            "spending_score": 39,
        }
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page_size": 101},
        {"age_min": 50, "age_max": 20},
        {"score_min": 0},
        {"genre": "Unknown"},
    ],
)
def test_rejects_invalid_query_parameters(client: TestClient, params: dict[str, object]) -> None:
    assert client.get("/customers", params=params).status_code == 422


def test_returns_not_found_for_unknown_customer(client: TestClient) -> None:
    response = client.get("/customers/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}
