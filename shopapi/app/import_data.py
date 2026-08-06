"""Import the shopping dataset CSV into the SQLite database.

Usage:
    python -m app.import_data [--csv PATH] [--db PATH]

Rows that fail validation are skipped and reported; the import is atomic
(all-or-nothing per run) thanks to a single transaction.
"""

import argparse
import csv
import sys
from pathlib import Path

from app.database import DEFAULT_CSV_PATH, get_connection, get_db_path, init_db

EXPECTED_COLUMNS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]


def parse_row(row: dict) -> tuple | None:
    """Validate one CSV row; return a tuple ready for insertion or None."""
    try:
        customer_id = int(row["CustomerID"])
        genre = row["Genre"].strip().capitalize()
        age = int(row["Age"])
        income = int(row["Annual Income (k$)"])
        score = int(row["Spending Score (1-100)"])
    except (KeyError, ValueError, AttributeError):
        return None
    if genre not in ("Male", "Female"):
        return None
    if not (1 <= age <= 120) or income < 0 or not (1 <= score <= 100):
        return None
    return (customer_id, genre, age, income, score)


def import_csv(csv_path: Path, db_path: Path) -> tuple[int, int]:
    """Import the CSV into the DB. Returns (imported, skipped) row counts."""
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [name.strip() for name in (reader.fieldnames or [])]
        if header != EXPECTED_COLUMNS:
            raise ValueError(
                f"Unexpected CSV columns: {header!r} (expected {EXPECTED_COLUMNS!r})"
            )
        parsed = [parse_row(row) for row in reader]

    valid = [p for p in parsed if p is not None]
    skipped = len(parsed) - len(valid)

    conn = get_connection(db_path)
    try:
        init_db(conn)
        with conn:  # single transaction
            conn.execute("DELETE FROM customers")
            conn.executemany(
                "INSERT INTO customers"
                " (customer_id, genre, age, annual_income_k, spending_score)"
                " VALUES (?, ?, ?, ?, ?)",
                valid,
            )
    finally:
        conn.close()
    return len(valid), skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import shopping dataset into SQLite")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--db", type=Path, default=None)
    args = parser.parse_args(argv)

    db_path = args.db or get_db_path()
    if not args.csv.exists():
        print(f"error: CSV file not found: {args.csv}", file=sys.stderr)
        return 1

    imported, skipped = import_csv(args.csv, db_path)
    print(f"Imported {imported} customers into {db_path} ({skipped} rows skipped)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
