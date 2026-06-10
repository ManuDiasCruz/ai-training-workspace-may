"""SQLite connection helpers and schema definition.

The database lives in a single file (``data/shopping.db`` by default) and
holds one table, ``customers``, mirroring the rows of the source CSV. The
location can be overridden with the ``SHOPPING_DB_PATH`` environment
variable, which is also how the test suite points the app at a throwaway
database.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "shopping.db"

SCHEMA_SQL = """
CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX idx_customers_genre  ON customers (genre);
CREATE INDEX idx_customers_age    ON customers (age);
CREATE INDEX idx_customers_income ON customers (annual_income_k);
CREATE INDEX idx_customers_score  ON customers (spending_score);
"""


def get_db_path() -> Path:
    """Resolve the database path, honouring the SHOPPING_DB_PATH override."""
    return Path(os.environ.get("SHOPPING_DB_PATH", DEFAULT_DB_PATH))


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a connection with rows accessible by column name."""
    path = Path(db_path) if db_path is not None else get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def rebuild_schema(conn: sqlite3.Connection) -> None:
    """Drop and recreate the customers table so imports are idempotent."""
    conn.execute("DROP TABLE IF EXISTS customers")
    conn.executescript(SCHEMA_SQL)
