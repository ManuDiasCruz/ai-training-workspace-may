from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolated_db(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("shopping-test")
    db_path = tmp_dir / "test.db"
    os.environ["SHOPPING_DATABASE_URL"] = f"sqlite:///{db_path}"

    csv_path = Path(__file__).resolve().parent.parent / "data" / "shopping.csv"
    os.environ["SHOPPING_CSV_PATH"] = str(csv_path)

    from app.db import Base, engine
    from app.import_data import import_csv

    Base.metadata.create_all(engine)
    import_csv(csv_path)
    yield


@pytest.fixture()
async def client():
    import httpx

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture()
def anyio_backend():
    return "asyncio"
