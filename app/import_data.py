from __future__ import annotations

import argparse
from pathlib import Path

from app.database import DEFAULT_CSV_PATH, DEFAULT_DB_PATH, import_customers_from_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import the shopping CSV into SQLite.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Path to the source CSV file. Defaults to {DEFAULT_CSV_PATH}.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to the SQLite database. Defaults to {DEFAULT_DB_PATH}.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    imported_count = import_customers_from_csv(csv_path=args.csv, db_path=args.db)
    print(f"Imported {imported_count} customer records into {args.db}")


if __name__ == "__main__":
    main()

