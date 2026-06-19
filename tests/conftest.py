from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from app.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    """The application runs on Uvicorn's asyncio backend in production."""
    return "asyncio"


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    database = tmp_path / "test.db"
    csv_path = Path(__file__).parents[1] / "data" / "shopping_customers.csv"
    app = create_app(database_path=database, seed_csv_path=csv_path)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as api_client:
            yield api_client
