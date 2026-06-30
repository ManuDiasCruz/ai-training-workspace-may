from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.import_data import import_csv
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "CustomerID,Genre,Age,Annual Income (k$),Spending Score (1-100)\n"
        "0001,Male,19,15,39\n"
        "0002,Female,31,70,81\n"
        "0003,Female,35,80,94\n"
        "0004,Male,64,90,3\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "test.db"
    imported = import_csv(csv_path, db_path)
    assert imported == 4
    with TestClient(create_app(db_path)) as test_client:
        yield test_client


def test_import_listing_pagination_and_filtering(client: TestClient) -> None:
    first_page = client.get("/customers", params={"page": 1, "page_size": 2})
    assert first_page.status_code == 200
    payload = first_page.json()
    assert payload["total"] == 4
    assert payload["total_pages"] == 2
    assert payload["has_next"] is True
    assert [item["customer_id"] for item in payload["items"]] == ["0001", "0002"]

    filtered = client.get(
        "/customers",
        params={
            "gender": "Female",
            "min_income": 75,
            "min_spending_score": 90,
            "search": "female",
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["customer_id"] == "0003"


def test_customer_lookup_and_not_found(client: TestClient) -> None:
    response = client.get("/customers/0002")
    assert response.status_code == 200
    assert response.json()["annual_income_k"] == 70

    missing = client.get("/customers/9999")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Customer not found"}


def test_rejects_invalid_parameters(client: TestClient) -> None:
    assert client.get("/customers", params={"page_size": 101}).status_code == 422
    response = client.get("/customers", params={"min_age": 50, "max_age": 20})
    assert response.status_code == 422
    assert "minimum" in response.json()["detail"]
    assert client.get("/customers/not-an-id").status_code == 422

