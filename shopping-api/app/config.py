"""Runtime configuration.

Values can be overridden with environment variables so the same code runs
locally, in tests (in-memory / temp DB) and in a container without edits.
"""
from __future__ import annotations

import os
from pathlib import Path

# Project root = the ``shopping-api`` directory (parent of the ``app`` package).
BASE_DIR = Path(__file__).resolve().parent.parent

# Location of the SQLite file. Override with SHOPPING_DB_PATH (e.g. for tests).
DB_PATH = Path(os.environ.get("SHOPPING_DB_PATH", BASE_DIR / "shopping.db"))

# Location of the source CSV used by the importer.
CSV_PATH = Path(os.environ.get("SHOPPING_CSV_PATH", BASE_DIR / "data" / "Shopping_data.csv"))


def database_url() -> str:
    """Return a SQLAlchemy connection URL for the configured SQLite path."""
    return f"sqlite:///{DB_PATH.as_posix()}"
