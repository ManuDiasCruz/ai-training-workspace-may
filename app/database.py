"""SQLite schema, connection helpers, and CSV import logic."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "shopping.db"
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY
        CHECK (customer_id GLOB '[0-9][0-9][0-9][0-9]'),
    gender TEXT NOT NULL
        CHECK (gender IN ('Male', 'Female')),
    age INTEGER NOT NULL
        CHECK (age BETWEEN 0 AND 120),
    annual_income_kusd INTEGER NOT NULL
        CHECK (annual_income_kusd >= 0),
    spending_score INTEGER NOT NULL
        CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_gender
    ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_age
    ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_annual_income
    ON customers (annual_income_kusd);
CREATE INDEX IF NOT EXISTS idx_customers_spending_score
    ON customers (spending_score);
"""

EXPECTED_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}


@dataclass(frozen=True)
class CustomerRow:
    customer_id: str
    gender: str
    age: int
    annual_income_kusd: int
    spending_score: int

    @classmethod
    def from_csv(cls, row: dict[str, str], line_number: int) -> "CustomerRow":
        """Parse and validate one source row before it reaches SQLite."""
        try:
            customer = cls(
                customer_id=row["CustomerID"].strip(),
                gender=row["Genre"].strip().title(),
                age=int(row["Age"]),
                annual_income_kusd=int(row["Annual Income (k$)"]),
                spending_score=int(row["Spending Score (1-100)"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid values on CSV line {line_number}") from exc

        if len(customer.customer_id) != 4 or not customer.customer_id.isdigit():
            raise ValueError(f"Invalid customer ID on CSV line {line_number}")
        if customer.gender not in {"Male", "Female"}:
            raise ValueError(f"Invalid gender on CSV line {line_number}")
        if not 0 <= customer.age <= 120:
            raise ValueError(f"Invalid age on CSV line {line_number}")
        if customer.annual_income_kusd < 0:
            raise ValueError(f"Invalid annual income on CSV line {line_number}")
        if not 1 <= customer.spending_score <= 100:
            raise ValueError(f"Invalid spending score on CSV line {line_number}")
        return customer


def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open a configured SQLite connection."""
    connection = sqlite3.connect(str(database_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """Create the database schema and indexes if they do not exist."""
    connection.executescript(SCHEMA_SQL)


def load_rows(csv_path: str | Path) -> list[CustomerRow]:
    """Read and validate all records from the source CSV."""
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        if columns != EXPECTED_COLUMNS:
            raise ValueError(
                "Unexpected CSV columns. "
                f"Expected {sorted(EXPECTED_COLUMNS)}, received {sorted(columns)}"
            )
        return [
            CustomerRow.from_csv(row, line_number)
            for line_number, row in enumerate(reader, start=2)
        ]


def import_dataset(
    connection: sqlite3.Connection,
    csv_path: str | Path = DEFAULT_DATASET_PATH,
    *,
    replace: bool = False,
) -> int:
    """Import the validated CSV in one transaction and return the row count."""
    rows = load_rows(csv_path)
    if len({row.customer_id for row in rows}) != len(rows):
        raise ValueError("The CSV contains duplicate customer IDs")

    with connection:
        if replace:
            connection.execute("DELETE FROM customers")
        connection.executemany(
            """
            INSERT INTO customers (
                customer_id, gender, age, annual_income_kusd, spending_score
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                gender = excluded.gender,
                age = excluded.age,
                annual_income_kusd = excluded.annual_income_kusd,
                spending_score = excluded.spending_score
            """,
            [
                (
                    row.customer_id,
                    row.gender,
                    row.age,
                    row.annual_income_kusd,
                    row.spending_score,
                )
                for row in rows
            ],
        )
    return len(rows)


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    csv_path: str | Path = DEFAULT_DATASET_PATH,
    *,
    force_import: bool = False,
) -> int:
    """Create a local database and seed it when empty (or when forced)."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        create_schema(connection)
        current_count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]
        if current_count == 0 or force_import:
            return import_dataset(connection, csv_path, replace=force_import)
        return current_count

