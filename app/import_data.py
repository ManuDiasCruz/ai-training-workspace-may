"""Validate the source CSV and persist it to SQLite."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .config import csv_path, database_path
from .database import connection, initialize_database

CSV_COLUMNS = (
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
)


@dataclass(frozen=True)
class CustomerRow:
    customer_id: str
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


class ImportValidationError(ValueError):
    """Raised when source data cannot satisfy the database schema."""


def _integer(value: str, *, field: str, line: int) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ImportValidationError(
            f"line {line}: {field} must be an integer (received {value!r})"
        ) from error


def _validated_row(source: dict[str, str], line: int) -> CustomerRow:
    customer_id = source["CustomerID"].strip()
    genre = source["Genre"].strip().title()
    age = _integer(source["Age"], field="Age", line=line)
    income = _integer(source["Annual Income (k$)"], field="Annual Income", line=line)
    score = _integer(
        source["Spending Score (1-100)"], field="Spending Score", line=line
    )

    if not customer_id or len(customer_id) > 32:
        raise ImportValidationError(f"line {line}: CustomerID must contain 1-32 characters")
    if genre not in {"Female", "Male"}:
        raise ImportValidationError(f"line {line}: unsupported Genre {genre!r}")
    if not 0 <= age <= 120:
        raise ImportValidationError(f"line {line}: Age must be in the range 0-120")
    if income < 0:
        raise ImportValidationError(f"line {line}: Annual Income must be non-negative")
    if not 1 <= score <= 100:
        raise ImportValidationError(f"line {line}: Spending Score must be in the range 1-100")

    return CustomerRow(customer_id, genre, age, income, score)


def read_csv(path: Path) -> list[CustomerRow]:
    """Read and validate all source rows before modifying the database."""
    if not path.is_file():
        raise ImportValidationError(f"CSV source does not exist: {path}")

    with path.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        if tuple(reader.fieldnames or ()) != CSV_COLUMNS:
            raise ImportValidationError(
                f"unexpected CSV header: expected {CSV_COLUMNS}, got {reader.fieldnames}"
            )
        rows = [_validated_row(row, line) for line, row in enumerate(reader, start=2)]

    if not rows:
        raise ImportValidationError("CSV source has no customer records")
    ids = [row.customer_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ImportValidationError("CSV source contains duplicate CustomerID values")
    return rows


def import_customers(source_csv: Path, target_database: Path) -> int:
    """Replace the customer snapshot atomically and return the imported row count."""
    rows = read_csv(source_csv)
    initialize_database(target_database)
    values = [
        (
            row.customer_id,
            row.genre,
            row.age,
            row.annual_income_k,
            row.spending_score,
        )
        for row in rows
    ]

    try:
        with connection(target_database) as db:
            with db:
                db.execute("DELETE FROM customers")
                db.executemany(
                    """
                    INSERT INTO customers (
                        customer_id, genre, age, annual_income_k, spending_score
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    values,
                )
    except sqlite3.IntegrityError as error:
        raise ImportValidationError(f"database constraint failed: {error}") from error
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=csv_path(), help="source CSV path")
    parser.add_argument(
        "--database", type=Path, default=database_path(), help="target SQLite path"
    )
    args = parser.parse_args()
    imported = import_customers(args.csv, args.database)
    print(f"Imported {imported} customers into {args.database}")


if __name__ == "__main__":
    main()
