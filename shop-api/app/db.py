"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from . import config


class DatabaseNotInitialized(RuntimeError):
    """Raised when the API is started before the dataset has been imported."""


def _readonly_uri(path: Path) -> str:
    # Path.as_uri() percent-encodes spaces and other characters that would
    # otherwise break the URI, which matters on Windows paths.
    return f"{path.as_uri()}?mode=ro"


def connect(*, read_only: bool = True) -> sqlite3.Connection:
    """Open a connection to the dataset database.

    The API only ever reads, so it opens the file in SQLite's read-only mode:
    a stray write is then rejected by the driver rather than silently mutating
    the imported dataset.
    """
    path = config.db_path()
    if read_only:
        if not path.exists():
            raise DatabaseNotInitialized(
                f"Database not found at {path}. "
                "Run 'python scripts/import_data.py' to create it."
            )
        conn = sqlite3.connect(_readonly_uri(path), uri=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_connection() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency yielding a per-request read-only connection."""
    conn = connect(read_only=True)
    try:
        yield conn
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    """Apply schema.sql to a writable connection."""
    conn.executescript(config.SCHEMA_PATH.read_text(encoding="utf-8"))
