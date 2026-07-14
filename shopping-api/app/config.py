"""Application configuration.

All settings are resolved from environment variables with sensible defaults so
the project runs locally out of the box while still being configurable for
other environments.
"""
from __future__ import annotations

import os
from pathlib import Path

# Project root: .../shopping-api
BASE_DIR = Path(__file__).resolve().parent.parent

# Location of the source dataset shipped with the repository.
DATA_FILE = Path(os.getenv("SHOPPING_DATA_FILE", BASE_DIR / "data" / "Shopping_data.csv"))

# Location of the SQLite database file. It is created by scripts/import_data.py.
DB_PATH = Path(os.getenv("SHOPPING_DB_PATH", BASE_DIR / "shopping.db"))

# SQLAlchemy database URL.
DATABASE_URL = os.getenv("SHOPPING_DATABASE_URL", f"sqlite:///{DB_PATH}")

# Pagination guard rails.
DEFAULT_PAGE_SIZE = int(os.getenv("SHOPPING_DEFAULT_PAGE_SIZE", "20"))
MAX_PAGE_SIZE = int(os.getenv("SHOPPING_MAX_PAGE_SIZE", "100"))
