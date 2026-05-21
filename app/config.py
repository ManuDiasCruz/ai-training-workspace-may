from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CSV_PATH = DATA_DIR / "shopping.csv"
DEFAULT_DB_PATH = DATA_DIR / "shopping.db"


def get_csv_path() -> Path:
    return Path(os.getenv("SHOPPING_CSV_PATH", str(DEFAULT_CSV_PATH))).expanduser().resolve()


def get_db_path() -> Path:
    return Path(os.getenv("SHOPPING_DB_PATH", str(DEFAULT_DB_PATH))).expanduser().resolve()
