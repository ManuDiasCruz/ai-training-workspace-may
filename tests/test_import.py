import sys

import pytest


def reload_app_modules():
    for module_name in [
        "scripts.import_data",
        "scripts",
        "app.main",
        "app.crud",
        "app.models",
        "app.schemas",
        "app.database",
        "app",
    ]:
        sys.modules.pop(module_name, None)


def test_import_rejects_missing_columns(tmp_path, monkeypatch):
    database_path = tmp_path / "shopping.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    reload_app_modules()

    from scripts.import_data import import_csv

    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text("CustomerID,Genre,Age\n0001,Male,19\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        import_csv(csv_path)


def test_import_is_atomic_when_a_row_is_invalid(tmp_path, monkeypatch):
    database_path = tmp_path / "shopping.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    reload_app_modules()

    from app.database import SessionLocal
    from app.models import Customer
    from scripts.import_data import import_csv

    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(
        "CustomerID,Genre,Age,Annual Income (k$),Spending Score (1-100)\n"
        "0001,Male,19,15,39\n"
        "0002,Unknown,21,15,81\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CSV line 3"):
        import_csv(csv_path)

    with SessionLocal() as session:
        assert session.query(Customer).count() == 0
