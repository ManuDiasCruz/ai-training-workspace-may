import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


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

    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import Base, engine
    from scripts.import_data import import_csv

    Base.metadata.create_all(bind=engine)
    import_csv(ROOT / "data" / "Shopping_data.csv")

    with TestClient(app) as c:
        yield c
