from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = PROJECT_DIR / "data" / "Shopping_data.csv"
EXPECTED_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_kusd INTEGER NOT NULL CHECK (annual_income_kusd >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_kusd);
CREATE INDEX IF NOT EXISTS idx_customers_spending ON customers (spending_score);
"""


def database_path() -> Path:
    return Path(os.getenv("SHOPPING_DATABASE_PATH", PROJECT_DIR / "shopping.db"))


def connect(path: Path | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(path or database_path())
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(path: Path | None = None) -> Path:
    target = path or database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect(target) as connection:
        connection.executescript(SCHEMA)
    return target


def import_csv(csv_path: Path = DEFAULT_CSV_PATH, db_path: Path | None = None) -> int:
    target = initialize_database(db_path)
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if set(reader.fieldnames or []) != EXPECTED_COLUMNS:
            raise ValueError(
                f"Unexpected CSV columns: {reader.fieldnames}; expected {sorted(EXPECTED_COLUMNS)}"
            )
        rows: list[tuple[str, str, int, int, int]] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                customer_id = row["CustomerID"].strip()
                gender = row["Genre"].strip().title()
                age = int(row["Age"])
                income = int(row["Annual Income (k$)"])
                score = int(row["Spending Score (1-100)"])
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid value on CSV line {line_number}") from exc
            if not customer_id or gender not in {"Male", "Female"}:
                raise ValueError(f"Invalid customer id or genre on CSV line {line_number}")
            rows.append((customer_id, gender, age, income, score))

    with connect(target) as connection:
        before = connection.total_changes
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
            rows,
        )
        return connection.total_changes - before


def seed_if_empty(csv_path: Path = DEFAULT_CSV_PATH, db_path: Path | None = None) -> None:
    target = initialize_database(db_path)
    with connect(target) as connection:
        count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    if count == 0:
        import_csv(csv_path, target)

