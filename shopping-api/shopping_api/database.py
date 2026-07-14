from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_kusd INTEGER NOT NULL CHECK (annual_income_kusd >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100),
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_customers_genre ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_kusd);
CREATE INDEX IF NOT EXISTS idx_customers_spending ON customers (spending_score);
"""

SOURCE_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.executescript(SCHEMA)


def import_csv(csv_path: Path, database_path: Path) -> int:
    """Validate and upsert every CSV row in one transaction."""
    initialize_database(database_path)
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if set(reader.fieldnames or []) != SOURCE_COLUMNS:
            raise ValueError(
                f"Unexpected CSV columns: {reader.fieldnames}. Expected {sorted(SOURCE_COLUMNS)}."
            )

        rows: list[tuple[str, str, int, int, int]] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                customer_id = row["CustomerID"].strip()
                genre = row["Genre"].strip().title()
                age = int(row["Age"])
                income = int(row["Annual Income (k$)"])
                score = int(row["Spending Score (1-100)"])
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid values on CSV line {line_number}") from exc

            if not customer_id or genre not in {"Male", "Female"}:
                raise ValueError(f"Invalid customer ID or genre on CSV line {line_number}")
            if not 0 <= age <= 120 or income < 0 or not 1 <= score <= 100:
                raise ValueError(f"Out-of-range value on CSV line {line_number}")
            rows.append((customer_id, genre, age, income, score))

    statement = """
        INSERT INTO customers (
            customer_id, genre, age, annual_income_kusd, spending_score
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET
            genre = excluded.genre,
            age = excluded.age,
            annual_income_kusd = excluded.annual_income_kusd,
            spending_score = excluded.spending_score,
            imported_at = CURRENT_TIMESTAMP
    """
    with connect(database_path) as connection:
        connection.executemany(statement, rows)
    return len(rows)
