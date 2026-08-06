"""SQLite configuration and schema for the shopping dataset."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "shopping.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY
        CHECK (length(customer_id) = 4 AND customer_id NOT GLOB '*[^0-9]*'),
    gender TEXT NOT NULL CHECK (gender IN ('Female', 'Male')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k_usd INTEGER NOT NULL CHECK (annual_income_k_usd >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_k_usd);
CREATE INDEX IF NOT EXISTS idx_customers_spending_score ON customers (spending_score);
"""


def get_database_path() -> Path:
    """Resolve the configurable database path at call time."""

    return Path(os.environ.get("SHOP_API_DATABASE", DEFAULT_DATABASE_PATH)).expanduser()


def connect(database_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection configured for API-friendly access."""

    path = Path(database_path) if database_path is not None else get_database_path()
    connection = sqlite3.connect(path, timeout=30, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def initialize_database(database_path: str | Path | None = None) -> Path:
    """Create the database, customer table, and filter indexes."""

    path = Path(database_path) if database_path is not None else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with connect(path) as connection:
        connection.executescript(SCHEMA)

    return path
