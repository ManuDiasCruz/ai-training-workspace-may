"""Command-line entry point for loading the shopping CSV into SQLite."""

from __future__ import annotations

import argparse
from pathlib import Path

from shopping_api.db import DEFAULT_CSV_PATH, configured_db_path, import_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="source CSV path")
    parser.add_argument("--db", type=Path, default=configured_db_path(), help="SQLite path")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="remove existing rows before importing the current CSV",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    imported = import_dataset(args.csv, args.db, replace=args.replace)
    print(f"Imported {imported} rows into {args.db}")


if __name__ == "__main__":
    main()
