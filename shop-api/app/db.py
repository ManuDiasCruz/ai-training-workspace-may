"""SQLite connection handling and schema bootstrap."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with row access by column name."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    """Apply schema.sql. Safe to run repeatedly (all statements are IF NOT EXISTS)."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def is_initialised(conn: sqlite3.Connection) -> bool:
    """True when the customers table exists and holds at least one row."""
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'customers'"
    ).fetchone()
    if table is None:
        return False
    return conn.execute("SELECT EXISTS (SELECT 1 FROM customers)").fetchone()[0] == 1
