"""CLI to (re)build the local SQLite database from the shopping CSV.

Usage (from the ``shopping-api`` directory):

    python -m scripts.import_data                 # use defaults
    python -m scripts.import_data --csv other.csv # custom source
    python -m scripts.import_data --append        # keep existing rows
"""
from __future__ import annotations

import argparse
import sys

from app.config import CSV_PATH, DB_PATH
from app.database import SessionLocal, init_db
from app.importer import DatasetError, import_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import the shopping dataset into SQLite.")
    parser.add_argument("--csv", default=str(CSV_PATH), help="Path to the source CSV file.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append rows instead of replacing the table (default: replace).",
    )
    args = parser.parse_args(argv)

    init_db()
    db = SessionLocal()
    try:
        count = import_csv(db, args.csv, replace=not args.append)
    except DatasetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Imported {count} customers into {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
