from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from shopping_api.importer import import_csv
from shopping_api.main import app

DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "shopping.csv"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    database_path = tmp_path / "shopping-test.db"
    monkeypatch.setenv("SHOPPING_DB_PATH", str(database_path))
    import_csv(DATASET_PATH, database_path)
    return database_path


@pytest.mark.anyio
async def test_lists_customers_with_pagination(database_path: Path) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/customers", params={"page": 2, "page_size": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 2
    assert payload["page_size"] == 5
    assert payload["total"] == 200
    assert payload["total_pages"] == 40
    assert payload["items"][0]["customer_id"] == "0006"


@pytest.mark.anyio
async def test_filters_and_searches_customers(database_path: Path) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/customers",
            params={"gender": "Female", "min_spending_score": 95, "q": "35"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert {item["customer_id"] for item in payload["items"]} == {"0012", "0020"}


@pytest.mark.anyio
async def test_returns_customer_and_not_found(database_path: Path) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/customers/0001")
        missing = await client.get("/customers/9999")

    assert response.status_code == 200
    assert response.json()["annual_income_k"] == 15
    assert missing.status_code == 404


@pytest.mark.anyio
async def test_rejects_invalid_ranges(database_path: Path) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/customers", params={"min_age": 50, "max_age": 20})

    assert response.status_code == 400
    assert response.json()["detail"] == "Minimum age cannot be greater than maximum age."
