"""End-to-end API tests against a temporary imported SQLite database."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from scripts.init_db import import_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = PROJECT_ROOT / "data" / "Shopping_data.csv"


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory):
    database_path = tmp_path_factory.mktemp("shopping-api") / "test.db"
    imported = import_csv(SOURCE_CSV, database_path)
    assert imported == 200

    with TestClient(create_app(database_path)) as test_client:
        yield test_client


def test_health_reports_imported_record_count(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ready",
        "customer_count": 200,
    }


def test_customer_listing_is_paginated(client: TestClient) -> None:
    response = client.get("/customers", params={"page": 2, "page_size": 3})

    assert response.status_code == 200
    payload = response.json()
    assert [item["customer_id"] for item in payload["items"]] == [
        "0004",
        "0005",
        "0006",
    ]
    assert payload["pagination"] == {
        "page": 2,
        "page_size": 3,
        "total_items": 200,
        "total_pages": 67,
    }


def test_customer_filters_can_be_combined(client: TestClient) -> None:
    response = client.get(
        "/customers",
        params={
            "gender": "Female",
            "min_age": 30,
            "max_age": 35,
            "min_income": 70,
            "min_spending_score": 70,
            "page_size": 100,
        },
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["gender"] == "Female" for item in items)
    assert all(30 <= item["age"] <= 35 for item in items)
    assert all(item["annual_income_k"] >= 70 for item in items)
    assert all(item["spending_score"] >= 70 for item in items)


def test_search_finds_a_partial_customer_id(client: TestClient) -> None:
    response = client.get("/customers", params={"search": "0194"})

    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == 1
    assert response.json()["items"][0]["customer_id"] == "0194"


def test_search_treats_sql_wildcards_as_literal_text(client: TestClient) -> None:
    response = client.get("/customers", params={"search": "%"})

    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == 0


def test_get_customer_and_not_found(client: TestClient) -> None:
    found = client.get("/customers/0001")
    missing = client.get("/customers/9999")

    assert found.status_code == 200
    assert found.json() == {
        "customer_id": "0001",
        "gender": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Customer not found"}


@pytest.mark.parametrize(
    ("params", "expected_detail"),
    [
        ({"min_age": 40, "max_age": 20}, "min_age cannot be greater than max_age"),
        (
            {"min_income": 80, "max_income": 20},
            "min_income cannot be greater than max_income",
        ),
        (
            {"min_spending_score": 90, "max_spending_score": 20},
            "min_spending_score cannot be greater than max_spending_score",
        ),
    ],
)
def test_inverted_filter_ranges_are_rejected(
    client: TestClient, params: dict[str, int], expected_detail: str
) -> None:
    response = client.get("/customers", params=params)

    assert response.status_code == 422
    assert response.json() == {"detail": expected_detail}


def test_query_limits_are_validated(client: TestClient) -> None:
    assert client.get("/customers", params={"page": 0}).status_code == 422
    assert client.get("/customers", params={"page_size": 101}).status_code == 422
    assert client.get("/customers", params={"gender": "Unknown"}).status_code == 422
    assert client.get("/customers", params={"search": "   "}).status_code == 422
    assert client.get("/customers/not-an-id").status_code == 422
