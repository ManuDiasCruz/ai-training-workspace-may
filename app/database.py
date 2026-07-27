from __future__ import annotations

import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "shopping.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100),
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customers_genre ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_annual_income
    ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_spending_score
    ON customers (spending_score);

CREATE TABLE IF NOT EXISTS dataset_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    rows_imported INTEGER NOT NULL CHECK (rows_imported >= 0),
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def database_path_from_env() -> Path:
    """Resolve the database path at call time so tests can override it."""
    configured = os.getenv("SHOP_API_DB_PATH")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DATABASE_PATH


def connect(database_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(database_path or database_path_from_env())
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(database_path: Path | str | None = None) -> Path:
    path = Path(database_path or database_path_from_env())
    with connect(path) as connection:
        connection.executescript(SCHEMA_SQL)
    return path

