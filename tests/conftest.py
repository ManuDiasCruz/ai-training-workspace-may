import asyncio
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class ASGISyncClient:
    def __init__(self, app):
        self.app = app

    async def _request(self, method: str, path: str, **kwargs):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, **kwargs)

    def get(self, path: str, **kwargs):
        return asyncio.run(self._request("GET", path, **kwargs))

    def post(self, path: str, **kwargs):
        return asyncio.run(self._request("POST", path, **kwargs))

    def delete(self, path: str, **kwargs):
        return asyncio.run(self._request("DELETE", path, **kwargs))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test_shopping.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    # Re-import modules under the temp DATABASE_URL.
    for mod in [
        "scripts.import_data",
        "scripts",
        "app.main",
        "app.crud",
        "app.models",
        "app.schemas",
        "app.database",
        "app",
    ]:
        sys.modules.pop(mod, None)

    from app.main import app
    from app.database import Base, engine
    from scripts.import_data import import_csv

    Base.metadata.create_all(bind=engine)
    import_csv(ROOT / "data" / "Shopping_data.csv")

    yield ASGISyncClient(app)
