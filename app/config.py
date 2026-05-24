from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DEFAULT_DB_PATH = DATA_DIR / "shopping.db"
DEFAULT_CSV_PATH = DATA_DIR / "shopping.csv"

DATABASE_URL = os.environ.get(
    "SHOPPING_DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH}",
)
CSV_PATH = Path(os.environ.get("SHOPPING_CSV_PATH", str(DEFAULT_CSV_PATH)))
