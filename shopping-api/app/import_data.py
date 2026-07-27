"""Validate and import the source CSV into SQLite."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

from app.db import PROJECT_ROOT, create_database, database_path

DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"
EXPECTED_HEADERS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]
CUSTOMER_ID_PATTERN = re.compile(r"\d{4}")


class ImportValidationError(ValueError):
    """Raised when source data does not satisfy the import contract."""


def parse_int(value: str, field: str, row_number: int, minimum: int, maximum: int | None = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ImportValidationError(f"row {row_number}: {field} must be an integer") from exc
    if result < minimum or (maximum is not None and result > maximum):
        bounds = f"{minimum}–{maximum}" if maximum is not None else f">= {minimum}"
        raise ImportValidationError(f"row {row_number}: {field} must be {bounds}")
    return result


def read_customers(csv_path: Path) -> list[tuple[str, str, int, int, int]]:
    """Read and validate every row before a database transaction begins."""
    customers: list[tuple[str, str, int, int, int]] = []
    seen_ids: set[str] = set()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != EXPECTED_HEADERS:
            raise ImportValidationError(
                f"expected headers {EXPECTED_HEADERS!r}; found {reader.fieldnames!r}"
            )
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ImportValidationError(f"row {row_number}: too many columns")
            if any(row.get(header) is None for header in EXPECTED_HEADERS):
                raise ImportValidationError(f"row {row_number}: missing column value")
            customer_id = row["CustomerID"].strip()
            if not CUSTOMER_ID_PATTERN.fullmatch(customer_id):
                raise ImportValidationError(f"row {row_number}: CustomerID must be four digits")
            if customer_id in seen_ids:
                raise ImportValidationError(f"row {row_number}: duplicate CustomerID {customer_id}")
            seen_ids.add(customer_id)
            gender = row["Genre"].strip()
            if not gender or len(gender) > 50:
                raise ImportValidationError(f"row {row_number}: Genre must be 1–50 characters")
            customers.append(
                (
                    customer_id,
                    gender,
                    parse_int(row["Age"], "Age", row_number, 0, 120),
                    parse_int(row["Annual Income (k$)"], "Annual Income (k$)", row_number, 0),
                    parse_int(row["Spending Score (1-100)"], "Spending Score (1-100)", row_number, 1, 100),
                )
            )
    if not customers:
        raise ImportValidationError("the CSV contains no customer rows")
    return customers


def import_csv(csv_path: Path, db_path: Path) -> int:
    """Replace the customer snapshot atomically after full source validation."""
    customers = read_customers(csv_path)
    connection = create_database(db_path)
    try:
        with connection:
            connection.execute("DELETE FROM customers")
            connection.executemany(
                """INSERT INTO customers
                   (customer_id, gender, age, annual_income_k, spending_score)
                   VALUES (?, ?, ?, ?, ?)""",
                customers,
            )
    finally:
        connection.close()
    return len(customers)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import the shopping CSV into SQLite.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="source CSV path")
    parser.add_argument("--db", type=Path, default=database_path(), help="destination SQLite path")
    args = parser.parse_args()
    try:
        count = import_csv(args.csv.resolve(), args.db.resolve())
    except (OSError, ImportValidationError, sqlite3.Error) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    print(f"Imported {count} customers into {args.db.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

