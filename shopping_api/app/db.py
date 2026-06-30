from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "shopping.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY
        CHECK (length(customer_id) = 4 AND customer_id NOT GLOB '*[^0-9]*'),
    gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers(gender);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers(age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers(annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_spending ON customers(spending_score);
"""


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection configured for dictionary-like rows."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Create the database schema and indexes if they do not exist."""
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)

