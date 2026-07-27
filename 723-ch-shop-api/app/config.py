"""Application configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "shopping.db"


def database_path() -> Path:
    """Return the configured SQLite database path."""

    configured_path = os.getenv("SHOPPING_DB_PATH")
    return Path(configured_path).expanduser().resolve() if configured_path else DEFAULT_DATABASE_PATH
