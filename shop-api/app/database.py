"""SQLite connection helpers and schema definition for the shop API."""

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "shop.db"

# The dataset is a single flat entity (one row per mall customer), so the
# schema is a single indexed table. CHECK constraints mirror the validation
# done at import time so bad data cannot enter through any path.
SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id              INTEGER PRIMARY KEY,
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_genre  ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age    ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_score  ON customers (spending_score);
"""


def get_db_path() -> Path:
    """Resolve the database path, overridable via the SHOP_API_DB env var."""
    return Path(os.environ.get("SHOP_API_DB", str(DEFAULT_DB_PATH)))


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with row access by column name."""
    path = Path(db_path) if db_path is not None else get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the schema if it does not exist yet."""
    conn.executescript(SCHEMA)
    conn.commit()


def db_is_ready() -> bool:
    """True when the database file exists and contains the customers table."""
    path = get_db_path()
    if not path.exists():
        return False
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'customers'"
        ).fetchone()
    return row is not None
