"""SQLite connection and schema management."""

from __future__ import annotations

import sqlite3
from pathlib import Path


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


def connect(database_path: str | Path) -> sqlite3.Connection:
    """Open a configured SQLite connection with dictionary-like rows."""

    connection = sqlite3.connect(database_path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(database_path: str | Path) -> None:
    """Create the database directory and schema when they do not exist."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        connection.executescript(SCHEMA)
