"""Import the shopping CSV dataset into the local SQLite database.

Usage:
    python scripts/import_data.py [--csv data/Shopping_data.csv] [--db data/shopping.db]

The import is idempotent: existing rows are replaced so the script can
be re-run safely after pulling a new version of the dataset.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import connect, init_schema  # noqa: E402

CSV_COLUMNS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]


def parse_row(row: dict[str, str], line_no: int) -> tuple[int, str, int, int, int]:
    try:
        customer_id = int(row["CustomerID"])
        genre = row["Genre"].strip().title()
        age = int(row["Age"])
        income = int(row["Annual Income (k$)"])
        score = int(row["Spending Score (1-100)"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"line {line_no}: malformed row {row!r}") from exc

    if genre not in ("Male", "Female"):
        raise ValueError(f"line {line_no}: unexpected genre {genre!r}")
    if not 1 <= age <= 120:
        raise ValueError(f"line {line_no}: age {age} out of range")
    if income < 0:
        raise ValueError(f"line {line_no}: negative income {income}")
    if not 1 <= score <= 100:
        raise ValueError(f"line {line_no}: spending score {score} out of range")

    return customer_id, genre, age, income, score


def import_csv(csv_path: Path, db_path: Path) -> int:
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV is missing expected columns: {missing}")
        records = [parse_row(row, i) for i, row in enumerate(reader, start=2)]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        init_schema(conn)
        with conn:
            conn.execute("DELETE FROM customers")
            conn.executemany(
                "INSERT INTO customers (id, genre, age, annual_income_k, spending_score)"
                " VALUES (?, ?, ?, ?, ?)",
                records,
            )
    finally:
        conn.close()
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=PROJECT_ROOT / "data" / "Shopping_data.csv")
    parser.add_argument("--db", type=Path, default=PROJECT_ROOT / "data" / "shopping.db")
    args = parser.parse_args()

    count = import_csv(args.csv, args.db)
    print(f"Imported {count} customers from {args.csv} into {args.db}")


if __name__ == "__main__":
    main()
