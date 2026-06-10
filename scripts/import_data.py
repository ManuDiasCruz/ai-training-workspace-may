from __future__ import annotations

import argparse
from pathlib import Path

from shopping_api.database import get_database_path
from shopping_api.importer import import_csv

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "shopping.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Import shopping customer data into SQLite.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--database", type=Path, default=get_database_path())
    args = parser.parse_args()

    imported = import_csv(args.csv, args.database)
    print(f"Imported {imported} records into {args.database}")


if __name__ == "__main__":
    main()
