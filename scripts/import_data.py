"""Import the shopping CSV dataset into the local SQLite database.

Usage (from the repository root)::

    python -m scripts.import_data [--csv data/Shopping_data.csv] [--db data/shopping.db]

The import is all-or-nothing and idempotent: every row is validated before
anything is written, the ``customers`` table is rebuilt from scratch on each
run, and the whole insert happens in a single transaction. Re-running the
script never duplicates rows.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/import_data.py` too
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import DEFAULT_DB_PATH, REPO_ROOT, connect, rebuild_schema

DEFAULT_CSV_PATH = REPO_ROOT / "data" / "Shopping_data.csv"

EXPECTED_HEADER = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]

VALID_GENRES = {"Male", "Female"}


class DatasetValidationError(Exception):
    """Raised when the CSV does not match the expected shape or constraints."""


def _parse_row(line_no: int, row: list[str]) -> tuple[int, str, int, int, int]:
    """Validate one CSV record and convert it to typed column values."""
    if len(row) != len(EXPECTED_HEADER):
        raise DatasetValidationError(
            f"line {line_no}: expected {len(EXPECTED_HEADER)} columns, got {len(row)}"
        )

    raw_id, genre, raw_age, raw_income, raw_score = (value.strip() for value in row)

    try:
        customer_id = int(raw_id)
        age = int(raw_age)
        income = int(raw_income)
        score = int(raw_score)
    except ValueError as exc:
        raise DatasetValidationError(f"line {line_no}: non-numeric value ({exc})") from exc

    if customer_id <= 0:
        raise DatasetValidationError(f"line {line_no}: CustomerID must be positive, got {customer_id}")
    if genre not in VALID_GENRES:
        raise DatasetValidationError(f"line {line_no}: Genre must be one of {sorted(VALID_GENRES)}, got {genre!r}")
    if not 1 <= age <= 120:
        raise DatasetValidationError(f"line {line_no}: Age must be between 1 and 120, got {age}")
    if income < 0:
        raise DatasetValidationError(f"line {line_no}: Annual Income must be >= 0, got {income}")
    if not 1 <= score <= 100:
        raise DatasetValidationError(f"line {line_no}: Spending Score must be between 1 and 100, got {score}")

    return customer_id, genre, age, income, score


def load_csv(csv_path: Path) -> list[tuple[int, str, int, int, int]]:
    """Read and validate the full dataset, failing fast on any bad record."""
    if not csv_path.exists():
        raise DatasetValidationError(f"CSV file not found: {csv_path}")

    with open(csv_path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            raise DatasetValidationError("CSV file is empty") from None

        if [column.strip() for column in header] != EXPECTED_HEADER:
            raise DatasetValidationError(
                f"unexpected header {header!r}; expected {EXPECTED_HEADER!r}"
            )

        records = [_parse_row(line_no, row) for line_no, row in enumerate(reader, start=2) if row]

    if not records:
        raise DatasetValidationError("CSV contains a header but no data rows")

    ids = [record[0] for record in records]
    if len(ids) != len(set(ids)):
        raise DatasetValidationError("duplicate CustomerID values found")

    return records


def import_csv(csv_path: Path, db_path: Path) -> int:
    """Rebuild the customers table from the CSV. Returns the row count."""
    records = load_csv(csv_path)

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = connect(db_path)
    try:
        with conn:  # one transaction: either everything lands or nothing does
            rebuild_schema(conn)
            conn.executemany(
                "INSERT INTO customers (customer_id, genre, age, annual_income_k, spending_score)"
                " VALUES (?, ?, ?, ?, ?)",
                records,
            )
        return len(records)
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Path to the source CSV")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the SQLite database to (re)build")
    args = parser.parse_args(argv)

    try:
        count = import_csv(args.csv, args.db)
    except DatasetValidationError as exc:
        print(f"Import aborted: {exc}", file=sys.stderr)
        return 1

    print(f"Imported {count} customers from {args.csv} into {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
