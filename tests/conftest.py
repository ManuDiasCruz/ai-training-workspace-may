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
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c
