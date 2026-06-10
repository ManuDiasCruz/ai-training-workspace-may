"""Application configuration.

Every setting can be overridden through an environment variable, which keeps
the service portable across local, test and CI environments without code
changes.
"""
from __future__ import annotations

import os
from pathlib import Path

# Project root: this file lives at <root>/app/config.py
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# --- Dataset -----------------------------------------------------------------
DATASET_PATH = Path(
    os.getenv("SHOPPING_DATASET_PATH", str(DATA_DIR / "Shopping_data.csv"))
)

# --- Database ----------------------------------------------------------------
# Default to a file-based SQLite database stored at the project root.
_DEFAULT_DB_PATH = BASE_DIR / "shopping.db"
DATABASE_URL = os.getenv("SHOPPING_DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


# When enabled, the API seeds the database from the CSV on startup if it is
# empty, so `uvicorn app.main:app` works out of the box with no extra steps.
AUTO_SEED = _as_bool(os.getenv("SHOPPING_AUTO_SEED", "true"))

# --- API metadata ------------------------------------------------------------
API_TITLE = "Shopping Customers API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "A small, production-style REST API over the Mall Customer Segmentation "
    "dataset. Supports listing, pagination, filtering, search and summary "
    "statistics for customer records."
)
