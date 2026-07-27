"""Command-line entry point for importing the source CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.config import PROJECT_ROOT, database_path
from app.importer import ImportValidationError, import_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Import shopping customers into SQLite")
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=PROJECT_ROOT / "data" / "Shopping_data.csv",
        help="Source CSV path (default: data/Shopping_data.csv)",
    )
    arguments = parser.parse_args()

    try:
        count = import_csv(arguments.csv_path)
    except (FileNotFoundError, ImportValidationError, RuntimeError) as exc:
        parser.exit(status=1, message=f"Import failed: {exc}\n")

    print(f"Imported {count} customers into {database_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
