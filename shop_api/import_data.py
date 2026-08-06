"""Validate and atomically import the original shopping CSV into SQLite."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from shop_api.database import PROJECT_ROOT, connect, get_database_path, initialize_database


DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"
EXPECTED_HEADERS = (
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
)


class DatasetImportError(ValueError):
    """Raised when a source CSV cannot be safely imported."""


@dataclass(frozen=True, slots=True)
class CustomerRecord:
    customer_id: str
    gender: str
    age: int
    annual_income_k_usd: int
    spending_score: int


def _parse_integer(value: str, *, field: str, line_number: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise DatasetImportError(
            f"Line {line_number}: {field} must be an integer; received {value!r}."
        ) from error


def _parse_record(row: dict[str, str], line_number: int) -> CustomerRecord:
    customer_id = row["CustomerID"].strip()
    gender = row["Genre"].strip()
    age = _parse_integer(row["Age"], field="Age", line_number=line_number)
    income = _parse_integer(
        row["Annual Income (k$)"],
        field="Annual Income (k$)",
        line_number=line_number,
    )
    spending_score = _parse_integer(
        row["Spending Score (1-100)"],
        field="Spending Score (1-100)",
        line_number=line_number,
    )

    if len(customer_id) != 4 or not customer_id.isascii() or not customer_id.isdigit():
        raise DatasetImportError(
            f"Line {line_number}: CustomerID must contain exactly four ASCII digits."
        )
    if gender not in {"Female", "Male"}:
        raise DatasetImportError(
            f"Line {line_number}: Genre must be either 'Female' or 'Male'."
        )
    if not 0 <= age <= 120:
        raise DatasetImportError(f"Line {line_number}: Age must be between 0 and 120.")
    if income < 0:
        raise DatasetImportError(
            f"Line {line_number}: Annual Income (k$) cannot be negative."
        )
    if not 0 <= spending_score <= 100:
        raise DatasetImportError(
            f"Line {line_number}: Spending Score (1-100) must be between 0 and 100."
        )

    return CustomerRecord(customer_id, gender, age, income, spending_score)


def read_customer_records(csv_path: str | Path = DEFAULT_CSV_PATH) -> list[CustomerRecord]:
    """Validate the source headers, values, and customer identifiers."""

    path = Path(csv_path)
    if not path.is_file():
        raise DatasetImportError(f"Shopping dataset was not found: {path}")

    try:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            headers = tuple(reader.fieldnames or ())
            if headers != EXPECTED_HEADERS:
                expected = ", ".join(EXPECTED_HEADERS)
                actual = ", ".join(headers) or "<empty file>"
                raise DatasetImportError(
                    f"Unexpected CSV headers. Expected [{expected}], received [{actual}]."
                )

            records: list[CustomerRecord] = []
            customer_ids: set[str] = set()
            for line_number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    raise DatasetImportError(
                        f"Line {line_number}: expected exactly {len(EXPECTED_HEADERS)} columns."
                    )

                record = _parse_record(row, line_number)
                if record.customer_id in customer_ids:
                    raise DatasetImportError(
                        f"Line {line_number}: duplicate CustomerID {record.customer_id!r}."
                    )
                customer_ids.add(record.customer_id)
                records.append(record)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise DatasetImportError(f"Could not read shopping dataset {path}: {error}") from error

    if not records:
        raise DatasetImportError("The shopping dataset contains no customer records.")

    return records


def import_dataset(
    csv_path: str | Path = DEFAULT_CSV_PATH,
    database_path: str | Path | None = None,
) -> tuple[Path, int]:
    """Replace the existing dataset in one atomic database transaction."""

    records = read_customer_records(csv_path)
    path = initialize_database(database_path)

    try:
        with connect(path) as connection:
            connection.execute("DELETE FROM customers")
            connection.executemany(
                """
                INSERT INTO customers (
                    customer_id, gender, age, annual_income_k_usd, spending_score
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.customer_id,
                        record.gender,
                        record.age,
                        record.annual_income_k_usd,
                        record.spending_score,
                    )
                    for record in records
                ],
            )
    except sqlite3.Error as error:
        raise DatasetImportError(f"Could not import customers into {path}: {error}") from error

    return path, len(records)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and import the shopping customer CSV into SQLite."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"CSV dataset path (default: {DEFAULT_CSV_PATH}).",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=get_database_path(),
        help="SQLite database path (default: SHOP_API_DATABASE or data/shopping.sqlite3).",
    )
    arguments = parser.parse_args()

    try:
        database_path, record_count = import_dataset(arguments.csv, arguments.database)
    except DatasetImportError as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1

    print(f"Imported {record_count} customers into {database_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

