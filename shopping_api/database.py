from __future__ import annotations

import os
import sqlite3
from collections.abc import AsyncIterator
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = BASE_DIR / "data" / "shopping.db"

SCHEMA_SQL = """
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


def get_database_path() -> Path:
    configured_path = os.getenv("SHOPPING_DB_PATH")
    return Path(configured_path) if configured_path else DEFAULT_DATABASE_PATH


def connect(database_path: Path | None = None) -> sqlite3.Connection:
    path = database_path or get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | None = None) -> None:
    with connect(database_path) as connection:
        connection.executescript(SCHEMA_SQL)


async def database_connection() -> AsyncIterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
