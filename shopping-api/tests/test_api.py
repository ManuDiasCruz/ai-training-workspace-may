from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.import_data import DEFAULT_CSV_PATH, import_csv
from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    database = tmp_path / "shopping.db"
    assert import_csv(DEFAULT_CSV_PATH, database) == 200
    monkeypatch.setenv("SHOPPING_DB_PATH", str(database))
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_paginated_listing(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok", "records": 200}
    response = client.get("/customers", params={"page": 2, "page_size": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 200
    assert body["total_pages"] == 67
    assert body["next_page"] == 3
    assert body["previous_page"] == 1
    assert [item["customer_id"] for item in body["items"]] == ["0004", "0005", "0006"]


def test_filters_and_search_are_combined(client: TestClient) -> None:
    response = client.get(
        "/customers",
        params={"gender": "female", "min_income": 100, "min_score": 80, "q": "female"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["customer_id"] for item in body["items"]] == ["0190", "0194"]


def test_detail_not_found_and_validation(client: TestClient) -> None:
    assert client.get("/customers/0001").json()["annual_income_k"] == 15
    assert client.get("/customers/9999").status_code == 404
    assert client.get("/customers/not-an-id").status_code == 422
    assert client.get("/customers", params={"page_size": 101}).status_code == 422
    assert client.get("/customers", params={"min_age": 50, "max_age": 20}).status_code == 422
    assert client.get("/customers", params={"q": "   "}).status_code == 422


def test_missing_database_returns_actionable_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOPPING_DB_PATH", str(tmp_path / "missing.db"))
    with TestClient(app) as client:
        response = client.get("/customers")
    assert response.status_code == 503
    assert "import command" in response.json()["detail"]
