"""SQLite configuration and schema for the shopping customer dataset."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "shopping.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY
        CHECK (length(customer_id) = 4 AND customer_id NOT GLOB '*[^0-9]*'),
    gender TEXT NOT NULL CHECK (length(trim(gender)) > 0),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers(gender COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers(age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers(annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_score ON customers(spending_score);
"""


def database_path() -> Path:
    """Return the configured path, resolving relative paths from the process cwd."""
    value = os.getenv("SHOPPING_DB_PATH")
    return Path(value).expanduser().resolve() if value else DEFAULT_DATABASE_PATH


def create_database(path: Path) -> sqlite3.Connection:
    """Create the database directory and schema, returning a writable connection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection


def open_readonly_database(path: Path) -> sqlite3.Connection:
    """Open an existing SQLite database without silently creating an empty file."""
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection

