from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import DEFAULT_DATASET_PATH
from app.import_data import import_customers
from app.main import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    database_path = tmp_path_factory.mktemp("database") / "test-shop.db"
    imported = import_customers(DEFAULT_DATASET_PATH, database_path)
    assert imported == 200

    with TestClient(create_app(database_path)) as test_client:
        yield test_client
