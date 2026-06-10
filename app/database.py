from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CSV_PATH = DATA_DIR / "Shopping_data.csv"
DEFAULT_DB_PATH = DATA_DIR / "shopping.db"

REQUIRED_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS shopping_customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_shopping_customers_genre
    ON shopping_customers (genre);

CREATE INDEX IF NOT EXISTS idx_shopping_customers_age
    ON shopping_customers (age);

CREATE INDEX IF NOT EXISTS idx_shopping_customers_income
    ON shopping_customers (annual_income_k);

CREATE INDEX IF NOT EXISTS idx_shopping_customers_spending_score
    ON shopping_customers (spending_score);
"""


def configured_db_path() -> Path:
    return Path(os.getenv("SHOPPING_API_DB_PATH", DEFAULT_DB_PATH))


def configured_csv_path() -> Path:
    return Path(os.getenv("SHOPPING_API_CSV_PATH", DEFAULT_CSV_PATH))


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else configured_db_path()
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: Path | str | None = None) -> Path:
    path = Path(db_path) if db_path else configured_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        connection.executescript(SCHEMA_SQL)
    return path


def _parse_int(value: str, field_name: str, row_number: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: {field_name} must be an integer") from exc


def _parse_customer(row: dict[str, str], row_number: int) -> tuple[str, str, int, int, int]:
    customer_id = (row.get("CustomerID") or "").strip()
    genre = (row.get("Genre") or "").strip()
    age = _parse_int((row.get("Age") or "").strip(), "Age", row_number)
    annual_income_k = _parse_int(
        (row.get("Annual Income (k$)") or "").strip(),
        "Annual Income (k$)",
        row_number,
    )
    spending_score = _parse_int(
        (row.get("Spending Score (1-100)") or "").strip(),
        "Spending Score (1-100)",
        row_number,
    )

    if not customer_id:
        raise ValueError(f"Row {row_number}: CustomerID is required")
    if genre not in {"Male", "Female"}:
        raise ValueError(f"Row {row_number}: Genre must be Male or Female")
    if not 0 <= age <= 120:
        raise ValueError(f"Row {row_number}: Age must be between 0 and 120")
    if annual_income_k < 0:
        raise ValueError(f"Row {row_number}: Annual Income (k$) cannot be negative")
    if not 1 <= spending_score <= 100:
        raise ValueError(
            f"Row {row_number}: Spending Score (1-100) must be between 1 and 100"
        )

    return customer_id, genre, age, annual_income_k, spending_score


def _read_customers(csv_path: Path) -> list[tuple[str, str, int, int, int]]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - fieldnames
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV is missing required columns: {missing}")
        return [_parse_customer(row, row_number) for row_number, row in enumerate(reader, 2)]


def import_customers_from_csv(
    csv_path: Path | str | None = None,
    db_path: Path | str | None = None,
) -> int:
    source_path = Path(csv_path) if csv_path else configured_csv_path()
    target_path = initialize_database(db_path)
    if not source_path.exists():
        raise FileNotFoundError(f"CSV file not found: {source_path}")

    customers = _read_customers(source_path)
    with connect(target_path) as connection:
        connection.execute("DELETE FROM shopping_customers")
        connection.executemany(
            """
            INSERT INTO shopping_customers (
                customer_id,
                genre,
                age,
                annual_income_k,
                spending_score
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            customers,
        )
    return len(customers)


def count_customers(db_path: Path | str | None = None) -> int:
    with connect(db_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM shopping_customers").fetchone()
    return int(row["total"])


def ensure_database(
    db_path: Path | str | None = None,
    csv_path: Path | str | None = None,
) -> Path:
    target_path = initialize_database(db_path)
    if count_customers(target_path) == 0:
        import_customers_from_csv(csv_path=csv_path, db_path=target_path)
    return target_path


def fetch_one(connection: sqlite3.Connection, query: str, params: Iterable[object]):
    return connection.execute(query, tuple(params)).fetchone()

