import os
import shutil
import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.import_data import import_csv  # noqa: E402

TMP_ROOT = Path(__file__).resolve().parent / ".tmp"


@pytest.fixture(scope="session")
def client():
    """TestClient wired to a throwaway database built from the real CSV."""
    tmp_dir = TMP_ROOT / uuid.uuid4().hex
    tmp_dir.mkdir(parents=True)
    db_path = tmp_dir / "shopping_test.db"
    import_csv(PROJECT_ROOT / "data" / "Shopping_data.csv", db_path)

    os.environ["SHOPAPI_DB_PATH"] = str(db_path)
    try:
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as test_client:
            yield test_client
    finally:
        os.environ.pop("SHOPAPI_DB_PATH", None)
        shutil.rmtree(tmp_dir, ignore_errors=True)
