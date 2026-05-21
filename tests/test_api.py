from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "shopping.csv"
APP_MODULES = ["app.config", "app.database", "app.import_data", "app.main"]


@pytest.fixture()
def app_instance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SHOPPING_DB_PATH", str(tmp_path / "shopping_test.db"))
    monkeypatch.setenv("SHOPPING_CSV_PATH", str(DATASET_PATH))

    for module_name in APP_MODULES:
        sys.modules.pop(module_name, None)

    from app.import_data import import_csv

    import_csv()

    from app.main import app

    yield app


async def _request(app, path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def _get(app, path: str) -> httpx.Response:
    return asyncio.run(_request(app, path))


def test_customers_list_supports_pagination_and_filters(app_instance) -> None:
    response = _get(
        app_instance,
        "/customers?page=2&page_size=5&genre=Female&min_age=20&max_age=40",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["page"] == 2
    assert payload["meta"]["page_size"] == 5
    assert len(payload["items"]) == 5
    assert all(item["genre"] == "Female" for item in payload["items"])
    assert all(20 <= item["age"] <= 40 for item in payload["items"])


def test_customer_lookup_and_summary(app_instance) -> None:
    customer_response = _get(app_instance, "/customers/1")
    assert customer_response.status_code == 200
    assert customer_response.json() == {
        "customer_id": "0001",
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }

    summary_response = _get(app_instance, "/summary")
    assert summary_response.status_code == 200
    assert summary_response.json()["total_customers"] == 200


def test_search_and_validation_errors(app_instance) -> None:
    search_response = _get(app_instance, "/search?q=137")
    assert search_response.status_code == 200
    assert search_response.json()["meta"]["total"] >= 1

    invalid_range = _get(app_instance, "/customers?min_age=50&max_age=20")
    assert invalid_range.status_code == 400

    missing_customer = _get(app_instance, "/customers/9999")
    assert missing_customer.status_code == 404
