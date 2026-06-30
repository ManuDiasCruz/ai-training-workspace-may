"""SQLite schema, connection helpers, and CSV import logic."""

from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "shopping.db"
EXPECTED_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY
        CHECK(length(customer_id) = 4 AND customer_id NOT GLOB '*[^0-9]*'),
    genre TEXT NOT NULL CHECK(genre IN ('Female', 'Male')),
    age INTEGER NOT NULL CHECK(age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK(annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK(spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_genre ON customers(genre);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers(age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers(annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_score ON customers(spending_score);
"""


class DatasetError(ValueError):
    """Raised when the source dataset violates its expected contract."""


def configured_db_path() -> Path:
    """Return the database path, allowing an environment override for tests."""

    return Path(os.environ.get("SHOPPING_DB_PATH", DEFAULT_DB_PATH))


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a configured SQLite connection with dictionary-like rows."""

    path = Path(db_path) if db_path is not None else configured_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """Create the database schema and indexes if they do not exist."""

    connection.executescript(SCHEMA)


def _parse_row(row: dict[str, str], line_number: int) -> tuple[str, str, int, int, int]:
    try:
        customer_id = row["CustomerID"].strip()
        genre = row["Genre"].strip().title()
        age = int(row["Age"])
        annual_income_k = int(row["Annual Income (k$)"])
        spending_score = int(row["Spending Score (1-100)"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetError(f"Invalid value on CSV line {line_number}: {exc}") from exc

    if len(customer_id) != 4 or not customer_id.isdigit():
        raise DatasetError(f"Invalid CustomerID on CSV line {line_number}: {customer_id!r}")
    if genre not in {"Female", "Male"}:
        raise DatasetError(f"Invalid Genre on CSV line {line_number}: {genre!r}")
    if not 0 <= age <= 120:
        raise DatasetError(f"Age outside 0-120 on CSV line {line_number}")
    if annual_income_k < 0:
        raise DatasetError(f"Annual income is negative on CSV line {line_number}")
    if not 1 <= spending_score <= 100:
        raise DatasetError(f"Spending score outside 1-100 on CSV line {line_number}")

    return customer_id, genre, age, annual_income_k, spending_score


def import_dataset(
    csv_path: Path | str = DEFAULT_CSV_PATH,
    db_path: Path | str | None = None,
    *,
    replace: bool = False,
) -> int:
    """Validate and upsert all CSV rows into SQLite, returning the source row count."""

    source = Path(csv_path)
    if not source.is_file():
        raise DatasetError(f"Dataset not found: {source}")

    with source.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if set(reader.fieldnames or []) != EXPECTED_COLUMNS:
            raise DatasetError(
                "Unexpected CSV columns. "
                f"Expected {sorted(EXPECTED_COLUMNS)}, got {reader.fieldnames!r}"
            )
        rows = [_parse_row(row, line_number) for line_number, row in enumerate(reader, start=2)]

    ids = [row[0] for row in rows]
    if len(ids) != len(set(ids)):
        raise DatasetError("Dataset contains duplicate CustomerID values")

    with connect(db_path) as connection:
        create_schema(connection)
        if replace:
            connection.execute("DELETE FROM customers")
        connection.executemany(
            """
            INSERT INTO customers (
                customer_id, genre, age, annual_income_k, spending_score
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                genre = excluded.genre,
                age = excluded.age,
                annual_income_k = excluded.annual_income_k,
                spending_score = excluded.spending_score
            """,
            rows,
        )

    return len(rows)


def initialize_database(
    db_path: Path | str | None = None,
    csv_path: Path | str = DEFAULT_CSV_PATH,
) -> None:
    """Create the database and load the dataset only when the table is empty."""

    with connect(db_path) as connection:
        create_schema(connection)
        count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    if count == 0:
        import_dataset(csv_path, db_path)

