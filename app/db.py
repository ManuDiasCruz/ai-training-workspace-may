"""SQLite connection management and schema bootstrap."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from app import config

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


class DatabaseNotReady(RuntimeError):
    """The database file or the customers table is missing/empty.

    Raised instead of leaking a raw sqlite3 error so the API can answer with
    an actionable 503 telling the caller to run the importer.
    """


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open a connection with dict-style rows and foreign keys enforced."""
    target = Path(path) if path is not None else config.db_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    # check_same_thread=False: FastAPI runs sync endpoints in a threadpool, so
    # the connection may be created and used on different worker threads. Each
    # request gets its own connection (see get_connection), so no single
    # connection is ever shared between concurrent requests.
    conn = sqlite3.connect(target, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes. Idempotent — safe to run on every import."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def customers_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'customers'"
    ).fetchone()
    return row is not None


def get_connection() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency yielding a per-request connection.

    Opening a SQLite connection is cheap (no handshake, no socket), so a
    connection pool would be complexity without benefit at this scale.
    """
    if not config.db_path().exists():
        raise DatabaseNotReady(
            f"Database not found at {config.db_path()}. "
            "Create it with: python -m scripts.import_dataset"
        )

    conn = connect()
    try:
        if not customers_table_exists(conn):
            raise DatabaseNotReady(
                "The 'customers' table does not exist. "
                "Create it with: python -m scripts.import_dataset"
            )
        yield conn
    finally:
        conn.close()
