"""SQLite access helpers shared by the API endpoints."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "shopping.db"


class DatabaseNotReadyError(RuntimeError):
    """Raised when the local database has not been initialized or is invalid."""


def get_database_path() -> Path:
    configured = os.getenv("SHOPPING_DB_PATH")
    return Path(configured) if configured else DEFAULT_DATABASE_PATH


@contextmanager
def open_database() -> Iterator[sqlite3.Connection]:
    database_path = get_database_path()
    if not database_path.is_file():
        raise DatabaseNotReadyError(
            "Shopping database is not initialized. Run "
            "`python -m shopping_api.scripts.import_data` first."
        )

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        yield connection
    except sqlite3.Error as exc:
        raise DatabaseNotReadyError(
            "The shopping database could not serve the request. "
            "Re-run the import command to rebuild it."
        ) from exc
    finally:
        if connection is not None:
            connection.close()
