"""Shared test fixtures.

The suite builds its own database in a temp directory using the real importer,
so the CSV -> SQLite path is exercised by every test run rather than mocked.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import config  # noqa: E402
from scripts.import_data import import_dataset  # noqa: E402

SOURCE_CSV = PROJECT_ROOT / "data" / "Shopping_data.csv"
EXPECTED_ROWS = 200


@pytest.fixture(scope="session")
def test_db() -> Iterator[Path]:
    """A freshly imported database, shared by the session (tests are read-only).

    The scratch directory is created inside the project rather than the system
    temp dir: it needs no privileges beyond the checkout itself, which keeps the
    suite runnable in restricted CI sandboxes.
    """
    scratch = Path(tempfile.mkdtemp(prefix=".pytest-tmp-", dir=PROJECT_ROOT))
    try:
        db_file = scratch / "test.db"
        report = import_dataset(SOURCE_CSV, db_file)
        assert report["row_count"] == EXPECTED_ROWS
        yield db_file
    finally:
        # ignore_errors: on Windows a lingering WAL handle can briefly hold a
        # file open; a leftover scratch dir must not fail an otherwise green run.
        shutil.rmtree(scratch, ignore_errors=True)


@pytest.fixture(scope="session")
def client(test_db: Path) -> Iterator[TestClient]:
    previous = os.environ.get(config.DB_ENV_VAR)
    os.environ[config.DB_ENV_VAR] = str(test_db)
    # Imported after the env var is set; the app reads the path per request, but
    # this keeps the ordering unambiguous.
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    if previous is None:
        os.environ.pop(config.DB_ENV_VAR, None)
    else:
        os.environ[config.DB_ENV_VAR] = previous
