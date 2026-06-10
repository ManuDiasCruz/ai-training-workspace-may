from __future__ import annotations

import csv
import re
from pathlib import Path

from shopping_api.database import connect, initialize_database

EXPECTED_COLUMNS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]
CUSTOMER_ID_PATTERN = re.compile(r"^\d{4}$")

UPSERT_SQL = """
INSERT INTO customers (
    customer_id,
    gender,
    age,
    annual_income_k,
    spending_score
) VALUES (?, ?, ?, ?, ?)
ON CONFLICT(customer_id) DO UPDATE SET
    gender = excluded.gender,
    age = excluded.age,
    annual_income_k = excluded.annual_income_k,
    spending_score = excluded.spending_score
"""


def _parse_integer(value: str, field_name: str, row_number: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: {field_name} must be an integer") from exc


def _normalize_row(row: dict[str, str], row_number: int) -> tuple[str, str, int, int, int]:
    customer_id = row["CustomerID"].strip()
    gender = row["Genre"].strip().title()
    age = _parse_integer(row["Age"], "Age", row_number)
    income = _parse_integer(row["Annual Income (k$)"], "Annual Income", row_number)
    score = _parse_integer(row["Spending Score (1-100)"], "Spending Score", row_number)

    if not CUSTOMER_ID_PATTERN.fullmatch(customer_id):
        raise ValueError(f"Row {row_number}: CustomerID must contain exactly four digits")
    if gender not in {"Male", "Female"}:
        raise ValueError(f"Row {row_number}: Genre must be Male or Female")
    if not 0 <= age <= 120:
        raise ValueError(f"Row {row_number}: Age must be between 0 and 120")
    if income < 0:
        raise ValueError(f"Row {row_number}: Annual Income must be non-negative")
    if not 1 <= score <= 100:
        raise ValueError(f"Row {row_number}: Spending Score must be between 1 and 100")

    return customer_id, gender, age, income, score


def import_csv(csv_path: Path, database_path: Path | None = None) -> int:
    initialize_database(database_path)

    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                f"Unexpected CSV columns: {reader.fieldnames}. Expected: {EXPECTED_COLUMNS}"
            )
        records = [
            _normalize_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        ]

    with connect(database_path) as connection:
        connection.executemany(UPSERT_SQL, records)

    return len(records)
