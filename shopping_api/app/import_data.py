from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from app.db import DEFAULT_DB_PATH, connect, initialize_database

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "Shopping_data.csv"
EXPECTED_HEADERS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]


@dataclass(frozen=True)
class CustomerRow:
    customer_id: str
    gender: str
    age: int
    annual_income_k: int
    spending_score: int

    def as_tuple(self) -> tuple[str, str, int, int, int]:
        return (
            self.customer_id,
            self.gender,
            self.age,
            self.annual_income_k,
            self.spending_score,
        )


def _parse_integer(value: str | None, field: str, row_number: int) -> int:
    try:
        return int(value or "")
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: {field} must be an integer") from exc


def _validate_row(raw: dict[str, str], row_number: int) -> CustomerRow:
    customer_id = (raw.get("CustomerID") or "").strip()
    gender = (raw.get("Genre") or "").strip()
    age = _parse_integer(raw.get("Age"), "Age", row_number)
    annual_income = _parse_integer(
        raw.get("Annual Income (k$)"), "Annual Income (k$)", row_number
    )
    spending_score = _parse_integer(
        raw.get("Spending Score (1-100)"), "Spending Score (1-100)", row_number
    )

    if not re.fullmatch(r"\d{4}", customer_id):
        raise ValueError(f"Row {row_number}: CustomerID must contain exactly four digits")
    if gender not in {"Male", "Female"}:
        raise ValueError(f"Row {row_number}: Genre must be Male or Female")
    if not 0 <= age <= 120:
        raise ValueError(f"Row {row_number}: Age must be between 0 and 120")
    if annual_income < 0:
        raise ValueError(f"Row {row_number}: Annual Income (k$) cannot be negative")
    if not 1 <= spending_score <= 100:
        raise ValueError(f"Row {row_number}: Spending Score must be between 1 and 100")

    return CustomerRow(customer_id, gender, age, annual_income, spending_score)


def read_csv(csv_path: str | Path) -> list[CustomerRow]:
    """Read and validate the source CSV before writing any rows."""
    records: list[CustomerRow] = []
    seen_ids: set[str] = set()
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != EXPECTED_HEADERS:
            raise ValueError(
                f"Unexpected CSV headers. Expected {EXPECTED_HEADERS}, got {reader.fieldnames}"
            )
        for row_number, raw in enumerate(reader, start=2):
            record = _validate_row(raw, row_number)
            if record.customer_id in seen_ids:
                raise ValueError(f"Row {row_number}: duplicate CustomerID {record.customer_id}")
            seen_ids.add(record.customer_id)
            records.append(record)

    if not records:
        raise ValueError("The CSV contains no customer records")
    return records


def import_csv(
    csv_path: str | Path = DEFAULT_CSV_PATH,
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    replace: bool = False,
) -> int:
    """Validate and transactionally upsert the source dataset into SQLite."""
    records = read_csv(csv_path)
    initialize_database(db_path)

    statement = """
        INSERT INTO customers (
            customer_id, gender, age, annual_income_k, spending_score
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET
            gender = excluded.gender,
            age = excluded.age,
            annual_income_k = excluded.annual_income_k,
            spending_score = excluded.spending_score
    """
    with connect(db_path) as connection:
        if replace:
            connection.execute("DELETE FROM customers")
        connection.executemany(statement, [record.as_tuple() for record in records])
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the shopping CSV into SQLite")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Source CSV path")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite path")
    parser.add_argument(
        "--replace", action="store_true", help="Delete existing records before import"
    )
    args = parser.parse_args()

    try:
        count = import_csv(args.csv, args.db, replace=args.replace)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Imported {count} customers into {args.db}")


if __name__ == "__main__":
    main()

