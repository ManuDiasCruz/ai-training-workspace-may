"""Validate the source CSV and persist its customer records in SQLite."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.config import DEFAULT_DATASET_PATH, get_database_path
from app.database import connect, initialize_database


EXPECTED_HEADERS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]
ALLOWED_GENDERS = {"Male", "Female"}


class DatasetValidationError(ValueError):
    """Raised when the source CSV does not match the expected data contract."""


@dataclass(frozen=True)
class CustomerRow:
    customer_id: str
    gender: str
    age: int
    annual_income_kusd: int
    spending_score: int

    def as_tuple(self) -> tuple[str, str, int, int, int]:
        return (
            self.customer_id,
            self.gender,
            self.age,
            self.annual_income_kusd,
            self.spending_score,
        )


def _parse_integer(value: str | None, field: str, row_number: int) -> int:
    try:
        return int((value or "").strip())
    except ValueError as exc:
        raise DatasetValidationError(
            f"Row {row_number}: {field} must be an integer."
        ) from exc


def _parse_row(source: dict[str, str], row_number: int) -> CustomerRow:
    customer_id = (source.get("CustomerID") or "").strip()
    if not re.fullmatch(r"\d{4}", customer_id):
        raise DatasetValidationError(
            f"Row {row_number}: CustomerID must contain exactly four digits."
        )

    gender = (source.get("Genre") or "").strip().title()
    if gender not in ALLOWED_GENDERS:
        raise DatasetValidationError(
            f"Row {row_number}: Genre must be one of {sorted(ALLOWED_GENDERS)}."
        )

    age = _parse_integer(source.get("Age"), "Age", row_number)
    income = _parse_integer(
        source.get("Annual Income (k$)"), "Annual Income (k$)", row_number
    )
    score = _parse_integer(
        source.get("Spending Score (1-100)"),
        "Spending Score (1-100)",
        row_number,
    )

    if not 0 <= age <= 120:
        raise DatasetValidationError(f"Row {row_number}: Age must be 0-120.")
    if income < 0:
        raise DatasetValidationError(
            f"Row {row_number}: Annual Income (k$) cannot be negative."
        )
    if not 1 <= score <= 100:
        raise DatasetValidationError(
            f"Row {row_number}: Spending Score must be 1-100."
        )

    return CustomerRow(customer_id, gender, age, income, score)


def read_dataset(dataset_path: str | Path) -> list[CustomerRow]:
    """Read and validate the complete CSV before any database mutation."""

    path = Path(dataset_path)
    if not path.is_file():
        raise DatasetValidationError(f"Dataset not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != EXPECTED_HEADERS:
            raise DatasetValidationError(
                "Unexpected CSV headers. "
                f"Expected {EXPECTED_HEADERS}, received {reader.fieldnames}."
            )
        rows = [_parse_row(row, row_number) for row_number, row in enumerate(reader, 2)]

    if not rows:
        raise DatasetValidationError("Dataset must contain at least one record.")
    if len({row.customer_id for row in rows}) != len(rows):
        raise DatasetValidationError("Dataset contains duplicate CustomerID values.")
    return rows


def import_customers(
    dataset_path: str | Path,
    database_path: str | Path,
    *,
    replace: bool = True,
) -> int:
    """Atomically import validated records and return the imported row count."""

    rows = read_dataset(dataset_path)
    initialize_database(database_path)

    try:
        with connect(database_path) as connection:
            if replace:
                connection.execute("DELETE FROM customers")
            connection.executemany(
                """
                INSERT INTO customers (
                    customer_id, gender, age, annual_income_kusd, spending_score
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [row.as_tuple() for row in rows],
            )
    except sqlite3.IntegrityError as exc:
        raise DatasetValidationError(
            "Import violates a database constraint; use --replace for a clean reload."
        ) from exc

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--database", type=Path, default=get_database_path())
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append instead of replacing existing customer records.",
    )
    args = parser.parse_args()

    imported = import_customers(args.dataset, args.database, replace=not args.append)
    print(f"Imported {imported} customers into {args.database}")


if __name__ == "__main__":
    main()

