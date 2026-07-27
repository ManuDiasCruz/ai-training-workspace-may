"""SQLite connection and schema initialization."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from app.config import PROJECT_ROOT, database_path


def connect() -> sqlite3.Connection:
    """Open a configured SQLite connection with safe defaults."""

    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Create database objects when they do not already exist."""

    schema = (PROJECT_ROOT / "schema.sql").read_text(encoding="utf-8")
    with connect() as connection:
        connection.executescript(schema)


def get_connection() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency that closes each request connection."""

    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
