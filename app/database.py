"""SQLite connection and schema helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Female', 'Male')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_genre ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_annual_income ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_spending_score ON customers (spending_score);
"""


def connect(path: Path) -> sqlite3.Connection:
    """Open a configured SQLite connection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection(path: Path) -> Iterator[sqlite3.Connection]:
    """Yield a database connection and close it after use."""
    db = connect(path)
    try:
        yield db
    finally:
        db.close()


def initialize_database(path: Path) -> None:
    """Create the database and idempotent schema."""
    with connection(path) as db:
        db.executescript(SCHEMA)
        db.commit()


def customer_count(path: Path) -> int:
    """Return the number of imported customers."""
    with connection(path) as db:
        row = db.execute("SELECT COUNT(*) AS count FROM customers").fetchone()
    return int(row["count"])
