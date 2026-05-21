"""Import the shopping CSV dataset into the local SQLite database."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.db import PROJECT_ROOT, SessionLocal, init_db
from app.models import Customer


DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"


def _parse_rows(reader: Iterable[dict[str, str]]) -> list[Customer]:
    rows: list[Customer] = []
    for raw in reader:
        rows.append(
            Customer(
                customer_id=int(raw["CustomerID"]),
                genre=raw["Genre"].strip(),
                age=int(raw["Age"]),
                annual_income_k=int(raw["Annual Income (k$)"]),
                spending_score=int(raw["Spending Score (1-100)"]),
            )
        )
    return rows


def import_csv(csv_path: Path = DEFAULT_CSV_PATH, *, session: Session | None = None) -> int:
    """Load the CSV into the customers table, replacing existing rows.

    Returns the number of inserted rows.
    """
    init_db()

    owns_session = session is None
    session = session or SessionLocal()
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            customers = _parse_rows(reader)

        session.query(Customer).delete()
        session.add_all(customers)
        session.commit()
        return len(customers)
    finally:
        if owns_session:
            session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import shopping CSV into SQLite.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Path to the CSV file (default: {DEFAULT_CSV_PATH}).",
    )
    args = parser.parse_args()

    count = import_csv(args.csv)
    print(f"Imported {count} customer rows from {args.csv}.")


if __name__ == "__main__":
    main()
