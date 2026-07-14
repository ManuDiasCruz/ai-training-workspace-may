from __future__ import annotations

import argparse
from pathlib import Path

from shopping_api.database import import_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Import shopping customers into SQLite")
    parser.add_argument(
        "--csv",
        type=Path,
        default=PROJECT_ROOT / "data" / "Shopping_data.csv",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=PROJECT_ROOT / "data" / "shopping.db",
    )
    args = parser.parse_args()
    imported = import_csv(args.csv, args.database)
    print(f"Imported {imported} rows into {args.database}")


if __name__ == "__main__":
    main()
