"""Validated CSV-to-SQLite import service."""

from __future__ import annotations

import csv
import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.database import connect, initialize_database


EXPECTED_COLUMNS = (
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
)


@dataclass(frozen=True)
class CustomerRow:
    customer_id: str
    gender: str
    age: int
    annual_income_k: int
    spending_score: int


class ImportValidationError(ValueError):
    """Raised when the source CSV does not satisfy the data contract."""


def _integer(value: str, field: str, row_number: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ImportValidationError(f"Row {row_number}: {field} must be an integer") from exc


def _parse_row(raw: dict[str, str], row_number: int) -> CustomerRow:
    customer_id = raw["CustomerID"].strip()
    gender = raw["Genre"].strip().title()
    age = _integer(raw["Age"], "Age", row_number)
    annual_income_k = _integer(raw["Annual Income (k$)"], "Annual Income (k$)", row_number)
    spending_score = _integer(raw["Spending Score (1-100)"], "Spending Score", row_number)

    if not customer_id or not customer_id.isdigit():
        raise ImportValidationError(f"Row {row_number}: CustomerID must contain digits")
    if gender not in {"Male", "Female"}:
        raise ImportValidationError(f"Row {row_number}: unsupported Genre {gender!r}")
    if not 0 <= age <= 120:
        raise ImportValidationError(f"Row {row_number}: Age must be between 0 and 120")
    if annual_income_k < 0:
        raise ImportValidationError(f"Row {row_number}: Annual Income must be non-negative")
    if not 1 <= spending_score <= 100:
        raise ImportValidationError(f"Row {row_number}: Spending Score must be between 1 and 100")

    return CustomerRow(customer_id, gender, age, annual_income_k, spending_score)


def read_customers(csv_path: Path) -> list[CustomerRow]:
    """Read and validate all customer rows before changing the database."""

    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise ImportValidationError(
                f"Unexpected columns. Expected {EXPECTED_COLUMNS}, received {tuple(reader.fieldnames or ())}"
            )
        rows = [_parse_row(row, index) for index, row in enumerate(reader, start=2)]

    identifiers = [row.customer_id for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ImportValidationError("CustomerID values must be unique")
    if not rows:
        raise ImportValidationError("The CSV contains no customer records")
    return rows


def import_csv(csv_path: Path) -> int:
    """Atomically replace customer data with validated CSV contents."""

    csv_path = csv_path.resolve()
    rows = read_customers(csv_path)
    checksum = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    initialize_database()

    try:
        with connect() as connection:
            connection.execute("DELETE FROM customers")
            connection.executemany(
                """
                INSERT INTO customers (
                    customer_id, gender, age, annual_income_k, spending_score
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.customer_id,
                        row.gender,
                        row.age,
                        row.annual_income_k,
                        row.spending_score,
                    )
                    for row in rows
                ],
            )
            connection.execute(
                """
                INSERT INTO import_runs (source_name, sha256, row_count)
                VALUES (?, ?, ?)
                """,
                (csv_path.name, checksum, len(rows)),
            )
    except sqlite3.DatabaseError as exc:
        raise RuntimeError(f"Database import failed: {exc}") from exc

    return len(rows)
