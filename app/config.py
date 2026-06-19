"""Runtime configuration resolved from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "shopping.db"
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "shopping_customers.csv"


def database_path() -> Path:
    """Return the configured SQLite file path."""
    return Path(os.getenv("SHOP_API_DATABASE_PATH", DEFAULT_DATABASE_PATH))


def csv_path() -> Path:
    """Return the configured source CSV path."""
    return Path(os.getenv("SHOP_API_CSV_PATH", DEFAULT_CSV_PATH))
