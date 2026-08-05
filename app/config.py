"""Application paths and environment-based configuration."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "shopping_customers.csv"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "shop.db"


def get_database_path() -> Path:
    """Return the configured SQLite path, defaulting to data/shop.db."""

    return Path(os.getenv("SHOP_API_DATABASE", DEFAULT_DATABASE_PATH))

