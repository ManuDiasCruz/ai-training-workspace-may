"""Runtime configuration, resolved from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "shopping.db"
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


@dataclass(frozen=True)
class Settings:
    """Resolved settings for one process."""

    db_path: Path
    csv_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=Path(os.getenv("SHOP_API_DB_PATH", str(DEFAULT_DB_PATH))),
            csv_path=Path(os.getenv("SHOP_API_CSV_PATH", str(DEFAULT_CSV_PATH))),
        )


def get_settings() -> Settings:
    """Read settings on every call so tests can point at a temporary database."""
    return Settings.from_env()
