"""Import the shopping CSV dataset into the local SQLite database.

Usage (from the shopping-api directory):

    python -m app.import_data                 # default CSV and DB locations
    python -m app.import_data --csv data/Shopping_data.csv --db data/shopping.db

The import is idempotent: it replaces the full contents of the customers
table inside a single transaction, so re-running it never duplicates rows.
"""

import argparse
import csv
import sys
from pathlib import Path

from .database import BASE_DIR, get_connection, get_db_path, init_schema

DEFAULT_CSV_PATH = BASE_DIR / "data" / "Shopping_data.csv"

EXPECTED_HEADER = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]

VALID_GENRES = {"Male", "Female"}


class DatasetError(ValueError):
    """Raised when the CSV file is missing, malformed or contains bad values."""


def _parse_row(raw: dict[str, str], line_no: int) -> tuple[int, str, int, int, int]:
    """Validate and convert one CSV row; raise DatasetError with line context."""
    try:
        customer_id = int(raw["CustomerID"])
        genre = raw["Genre"].strip().title()
        age = int(raw["Age"])
        annual_income_k = int(raw["Annual Income (k$)"])
        spending_score = int(raw["Spending Score (1-100)"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetError(f"line {line_no}: could not parse row ({exc})") from exc

    if customer_id <= 0:
        raise DatasetError(f"line {line_no}: CustomerID must be positive, got {customer_id}")
    if genre not in VALID_GENRES:
        raise DatasetError(f"line {line_no}: Genre must be Male or Female, got {raw['Genre']!r}")
    if not 1 <= age <= 120:
        raise DatasetError(f"line {line_no}: Age out of range 1-120, got {age}")
    if annual_income_k < 0:
        raise DatasetError(f"line {line_no}: Annual Income must be >= 0, got {annual_income_k}")
    if not 1 <= spending_score <= 100:
        raise DatasetError(f"line {line_no}: Spending Score out of range 1-100, got {spending_score}")

    return customer_id, genre, age, annual_income_k, spending_score


def import_csv(csv_path: Path | str = DEFAULT_CSV_PATH, db_path: Path | str | None = None) -> int:
    """Load the CSV into SQLite, replacing existing rows. Returns rows imported."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise DatasetError(f"CSV file not found: {csv_path}")

    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [name.strip() for name in reader.fieldnames or []]
        if header != EXPECTED_HEADER:
            raise DatasetError(
                f"Unexpected CSV header {header!r}; expected {EXPECTED_HEADER!r}"
            )
        rows = [_parse_row(raw, line_no) for line_no, raw in enumerate(reader, start=2)]

    if not rows:
        raise DatasetError(f"CSV file contains no data rows: {csv_path}")

    conn = get_connection(db_path)
    try:
        init_schema(conn)
        with conn:  # single transaction: all-or-nothing
            conn.execute("DELETE FROM customers")
            conn.executemany(
                "INSERT INTO customers"
                " (customer_id, genre, age, annual_income_k, spending_score)"
                " VALUES (?, ?, ?, ?, ?)",
                rows,
            )
    finally:
        conn.close()
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH, help="path to the source CSV file")
    parser.add_argument("--db", default=None, help="path to the SQLite database file")
    args = parser.parse_args(argv)

    try:
        count = import_csv(args.csv, args.db)
    except DatasetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    db_path = Path(args.db) if args.db else get_db_path()
    print(f"Imported {count} customers from {args.csv} into {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
