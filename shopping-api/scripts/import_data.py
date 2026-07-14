"""Import the shopping dataset (CSV) into the local SQLite database.

Usage (from the ``shopping-api`` directory):

    python -m scripts.import_data                # use the bundled CSV
    python -m scripts.import_data path/to.csv    # use a custom CSV

The import is idempotent: it (re)creates the schema and replaces all rows so
running it repeatedly always yields the same, fully-populated database.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from sqlalchemy import delete

from app.config import DATA_FILE
from app.database import Base, SessionLocal, engine
from app.models import Customer

# Map the (human, spacey) CSV headers to ORM attribute names.
COLUMN_MAP = {
    "CustomerID": "customer_id",
    "Genre": "gender",
    "Age": "age",
    "Annual Income (k$)": "annual_income",
    "Spending Score (1-100)": "spending_score",
}

REQUIRED_HEADERS = set(COLUMN_MAP)


def _parse_row(row: dict[str, str], line_no: int) -> Customer:
    """Validate and convert one CSV row into a ``Customer`` instance."""
    try:
        customer_id = row["CustomerID"].strip()
        gender = row["Genre"].strip()
        age = int(row["Age"])
        annual_income = int(row["Annual Income (k$)"])
        spending_score = int(row["Spending Score (1-100)"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Invalid data on CSV line {line_no}: {exc}") from exc

    if not customer_id:
        raise ValueError(f"Empty CustomerID on CSV line {line_no}")
    if gender not in ("Male", "Female"):
        raise ValueError(f"Unexpected gender '{gender}' on CSV line {line_no}")

    return Customer(
        customer_id=customer_id,
        gender=gender,
        age=age,
        annual_income=annual_income,
        spending_score=spending_score,
    )


def load_rows(csv_path: Path) -> list[Customer]:
    """Read and validate every row from ``csv_path``."""
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = {h.strip() for h in (reader.fieldnames or [])}
        missing = REQUIRED_HEADERS - headers
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        # Reset fieldnames to their stripped form so lookups are consistent.
        reader.fieldnames = [h.strip() for h in reader.fieldnames]  # type: ignore[assignment]
        return [_parse_row(row, i) for i, row in enumerate(reader, start=2)]


def import_data(csv_path: Path) -> int:
    """Create the schema and (re)load all rows. Returns the number imported."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    customers = load_rows(csv_path)

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.execute(delete(Customer))  # start from a clean slate
        session.add_all(customers)
        session.commit()

    return len(customers)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    csv_path = Path(argv[0]) if argv else DATA_FILE

    count = import_data(csv_path)
    print(f"Imported {count} customers from {csv_path} into the database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
