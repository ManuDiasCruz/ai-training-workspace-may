"""SQLite connection and schema helpers for the shopping API."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = Path("data/shopping.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY
        CHECK (length(customer_id) = 4 AND customer_id NOT GLOB '*[^0-9]*'),
    gender TEXT NOT NULL CHECK (gender IN ('Female', 'Male')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_spending ON customers (spending_score);
"""


def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open a configured SQLite connection and return rows by column name."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    """Create the application schema when it does not already exist."""

    with connect(database_path) as connection:
        connection.executescript(SCHEMA_SQL)
