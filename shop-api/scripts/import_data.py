"""Import the shopping CSV dataset into the local SQLite database.

Usage (from the shop-api directory):

    python scripts/import_data.py
    python scripts/import_data.py --csv data/Shopping_data.csv --db data/shop.db

The import is idempotent: rows are upserted by customer id, so running the
script twice leaves the database unchanged.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import DEFAULT_DB_PATH, get_connection, init_db

DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "Shopping_data.csv"

EXPECTED_HEADER = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]

VALID_GENRES = {"Male", "Female"}


class RowError(ValueError):
    """A CSV row that fails validation."""


def parse_row(row: dict[str, str]) -> tuple[int, str, int, int, int]:
    """Validate one CSV row and convert it to typed column values."""
    try:
        customer_id = int(row["CustomerID"])
        genre = row["Genre"].strip().title()
        age = int(row["Age"])
        income = int(row["Annual Income (k$)"])
        score = int(row["Spending Score (1-100)"])
    except (KeyError, ValueError) as exc:
        raise RowError(f"malformed row {row!r}: {exc}") from exc

    if customer_id <= 0:
        raise RowError(f"CustomerID must be positive, got {customer_id}")
    if genre not in VALID_GENRES:
        raise RowError(f"Genre must be one of {sorted(VALID_GENRES)}, got {genre!r}")
    if not 1 <= age <= 120:
        raise RowError(f"Age out of range 1-120: {age}")
    if income < 0:
        raise RowError(f"Annual income cannot be negative: {income}")
    if not 1 <= score <= 100:
        raise RowError(f"Spending score out of range 1-100: {score}")

    return customer_id, genre, age, income, score


def import_csv(csv_path: Path, db_path: Path) -> int:
    """Load the CSV into the database and return the number of rows imported."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or [f.strip() for f in reader.fieldnames] != EXPECTED_HEADER:
            raise RowError(
                f"unexpected CSV header {reader.fieldnames!r}, expected {EXPECTED_HEADER!r}"
            )
        records = [parse_row(row) for row in reader]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as conn:
        init_db(conn)
        conn.executemany(
            """
            INSERT INTO customers (id, genre, age, annual_income_k, spending_score)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                genre = excluded.genre,
                age = excluded.age,
                annual_income_k = excluded.annual_income_k,
                spending_score = excluded.spending_score
            """,
            records,
        )
        conn.commit()
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Path to the dataset CSV")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the SQLite database")
    args = parser.parse_args()

    count = import_csv(args.csv, args.db)
    print(f"Imported {count} customers from {args.csv} into {args.db}")


if __name__ == "__main__":
    main()
