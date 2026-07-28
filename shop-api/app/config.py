"""Configuration for the shopping-dataset API.

Paths are resolved on every call (not cached at import time) so tests and
deployments can redirect them with environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent

SCHEMA_PATH = PACKAGE_DIR / "schema.sql"

#: Environment variable overriding the SQLite database location.
DB_ENV_VAR = "SHOP_API_DB"
#: Environment variable overriding the source CSV location.
CSV_ENV_VAR = "SHOP_API_CSV"

DEFAULT_DB_PATH = PROJECT_ROOT / "shop.db"
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"

# Pagination bounds. MAX_PAGE_SIZE caps how much a single request can pull.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

API_PREFIX = "/api/v1"


def db_path() -> Path:
    """Filesystem location of the SQLite database."""
    return Path(os.environ.get(DB_ENV_VAR) or DEFAULT_DB_PATH)


def csv_path() -> Path:
    """Filesystem location of the source dataset CSV."""
    return Path(os.environ.get(CSV_ENV_VAR) or DEFAULT_CSV_PATH)
