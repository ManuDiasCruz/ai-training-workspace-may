"""CLI entry point: create the schema and load the dataset into the database.

Examples:
    python -m scripts.init_db                  # seed bundled dataset
    python -m scripts.init_db --csv other.csv  # seed a custom CSV
    python scripts/init_db.py                  # direct invocation also works
"""
from __future__ import annotations

import argparse
import os
import sys

# Allow `python scripts/init_db.py` by making the project root importable
# regardless of the current working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config  # noqa: E402
from app import models  # noqa: E402,F401  (import registers the ORM table)
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.seed import count_customers, seed_database  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialise and seed the shopping database."
    )
    parser.add_argument(
        "--csv",
        default=str(config.DATASET_PATH),
        help="Path to the dataset CSV (default: the bundled dataset).",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Append rows instead of replacing existing data.",
    )
    args = parser.parse_args(argv)

    print(f"Database URL : {config.DATABASE_URL}")
    print(f"Dataset CSV  : {args.csv}")

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        inserted = seed_database(session, args.csv, replace=not args.keep_existing)
        total = count_customers(session)

    print(f"Inserted {inserted} record(s); table now holds {total} customer(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
