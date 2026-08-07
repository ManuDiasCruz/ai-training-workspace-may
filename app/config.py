"""Runtime configuration.

Paths are resolved through functions rather than module-level constants so
that the environment can be changed after import — which is what the test
suite does to point the app at a throwaway database.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "shopping.db"

# Pagination bounds. MAX_PAGE_SIZE caps how much a single request can pull so
# a stray ?page_size=100000 cannot be used to dump the whole table at once.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Ceiling for ?page. Guards against absurd OFFSET values.
MAX_PAGE = 10_000


def csv_path() -> Path:
    """Source CSV location. Override with SHOPAPI_CSV_PATH."""
    return Path(os.getenv("SHOPAPI_CSV_PATH") or DEFAULT_CSV_PATH)


def db_path() -> Path:
    """SQLite database location. Override with SHOPAPI_DB_PATH."""
    return Path(os.getenv("SHOPAPI_DB_PATH") or DEFAULT_DB_PATH)
