"""SQLite helpers for the shop API.

The database lives next to the project by default; tests and the import
script can point somewhere else via the SHOP_API_DB environment variable.
"""

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "shop.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id    INTEGER PRIMARY KEY,
    genre          TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age            INTEGER NOT NULL CHECK (age > 0),
    annual_income  INTEGER NOT NULL CHECK (annual_income >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_genre ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income);
CREATE INDEX IF NOT EXISTS idx_customers_score ON customers (spending_score);
"""


def get_db_path() -> Path:
    return Path(os.environ.get("SHOP_API_DB", DEFAULT_DB_PATH))


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
