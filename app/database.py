from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from .config import get_db_path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score >= 0 AND spending_score <= 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_genre ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_spending_score ON customers (spending_score);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or get_db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def create_schema(db_path: Path | None = None) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.commit()


def customer_count(db_path: Path | None = None) -> int:
    create_schema(db_path)
    with connect(db_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM customers").fetchone()
    return int(row["total"])


def get_db() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
