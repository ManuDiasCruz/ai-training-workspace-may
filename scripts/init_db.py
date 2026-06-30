"""Create the SQLite database and import the source shopping CSV."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from app.database import DEFAULT_DATABASE_PATH, connect, initialize_database


DEFAULT_CSV_PATH = Path("data/Shopping_data.csv")
EXPECTED_HEADERS = (
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


def parse_row(raw: dict[str, str], row_number: int) -> CustomerRow:
    """Validate and normalize one source CSV row."""

    try:
        customer_id = raw["CustomerID"].strip()
        gender = raw["Genre"].strip().title()
        age = int(raw["Age"])
        annual_income_k = int(raw["Annual Income (k$)"])
        spending_score = int(raw["Spending Score (1-100)"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid values on CSV row {row_number}: {exc}") from exc

    if len(customer_id) != 4 or not customer_id.isdigit():
        raise ValueError(f"Invalid CustomerID on CSV row {row_number}: {customer_id!r}")
    if gender not in {"Female", "Male"}:
        raise ValueError(f"Invalid gender on CSV row {row_number}: {gender!r}")
    if not 0 <= age <= 120:
        raise ValueError(f"Age out of range on CSV row {row_number}: {age}")
    if annual_income_k < 0:
        raise ValueError(
            f"Annual income cannot be negative on CSV row {row_number}: "
            f"{annual_income_k}"
        )
    if not 1 <= spending_score <= 100:
        raise ValueError(
            f"Spending score out of range on CSV row {row_number}: {spending_score}"
        )

    return CustomerRow(
        customer_id=customer_id,
        gender=gender,
        age=age,
        annual_income_k=annual_income_k,
        spending_score=spending_score,
    )


def read_customers(csv_path: str | Path) -> list[CustomerRow]:
    """Read and validate every customer in the supplied CSV."""

    with Path(csv_path).open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        headers = tuple(reader.fieldnames or ())
        if headers != EXPECTED_HEADERS:
            raise ValueError(
                "Unexpected CSV headers. "
                f"Expected {EXPECTED_HEADERS!r}, received {headers!r}."
            )
        customers = [parse_row(row, index) for index, row in enumerate(reader, 2)]

    if not customers:
        raise ValueError("The CSV does not contain any customer rows.")
    if len({customer.customer_id for customer in customers}) != len(customers):
        raise ValueError("The CSV contains duplicate CustomerID values.")
    return customers


def import_csv(
    csv_path: str | Path = DEFAULT_CSV_PATH,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Upsert the CSV into SQLite in one transaction and return its row count."""

    customers = read_customers(csv_path)
    initialize_database(database_path)

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
    values = [
        (
            customer.customer_id,
            customer.gender,
            customer.age,
            customer.annual_income_k,
            customer.spending_score,
        )
        for customer in customers
    ]

    with connect(database_path) as connection:
        connection.executemany(statement, values)

    return len(customers)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the shopping SQLite database from the source CSV."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE_PATH)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    imported = import_csv(args.csv, args.database)
    print(f"Imported {imported} customers into {args.database}")


if __name__ == "__main__":
    main()
