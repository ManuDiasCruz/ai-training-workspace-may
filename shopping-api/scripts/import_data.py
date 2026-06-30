"""Load the shopping dataset CSV into the local SQLite database.

Usage:
    python -m scripts.import_data            # uses data/Shopping_data.csv
    python -m scripts.import_data path.csv   # custom CSV path

The script is idempotent: it (re)creates the schema and replaces all rows,
so running it repeatedly always yields the same clean dataset.
"""
import csv
import sys
from pathlib import Path

# Allow running as `python scripts/import_data.py` as well as `-m`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "Shopping_data.csv"

# Map source CSV headers -> ORM attribute names.
COLUMN_MAP = {
    "CustomerID": "customer_id",
    "Genre": "genre",
    "Age": "age",
    "Annual Income (k$)": "annual_income",
    "Spending Score (1-100)": "spending_score",
}


def load_rows(csv_path: Path):
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = set(COLUMN_MAP) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing expected columns: {sorted(missing)}")
        for line_no, raw in enumerate(reader, start=2):
            try:
                yield models.Customer(
                    customer_id=raw["CustomerID"].strip(),
                    genre=raw["Genre"].strip(),
                    age=int(raw["Age"]),
                    annual_income=int(raw["Annual Income (k$)"]),
                    spending_score=int(raw["Spending Score (1-100)"]),
                )
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Bad data on CSV line {line_no}: {raw} ({exc})") from exc


def main(csv_path: Path = DEFAULT_CSV) -> int:
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    # Recreate schema for a clean, idempotent import.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        customers = list(load_rows(csv_path))
        session.bulk_save_objects(customers)
        session.commit()
        count = session.query(models.Customer).count()
    finally:
        session.close()

    print(f"Imported {count} customer records from {csv_path}")
    return count


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    main(path)
