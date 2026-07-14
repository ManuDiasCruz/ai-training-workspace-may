"""Command-line entry point for importing the shopping CSV into SQLite."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.database import (
    DEFAULT_DATABASE_PATH,
    DEFAULT_DATASET_PATH,
    initialize_database,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="SQLite database path (default: data/shopping.db)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Source CSV path (default: data/Shopping_data.csv)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing records before importing the source data",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = initialize_database(
        args.database,
        args.csv,
        force_import=args.replace,
    )
    print(f"Database ready at {args.database} ({count} customer records).")


if __name__ == "__main__":
    main()
