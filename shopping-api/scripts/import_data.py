"""Import Shopping_data.csv into the local SQLite database.

Usage (from the shopping-api directory):

    python scripts/import_data.py [--csv data/Shopping_data.csv]

The import is idempotent: rows are upserted by CustomerID, so running it
twice does not duplicate data. Rows that fail validation are skipped and
reported at the end.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Customer  # noqa: E402

CSV_COLUMNS = {
    "CustomerID": "id",
    "Genre": "genre",
    "Age": "age",
    "Annual Income (k$)": "annual_income_k",
    "Spending Score (1-100)": "spending_score",
}


def parse_row(row: dict, line_number: int) -> Customer:
    """Convert one CSV row into a Customer, raising ValueError when invalid."""
    missing = [col for col in CSV_COLUMNS if not (row.get(col) or "").strip()]
    if missing:
        raise ValueError(f"line {line_number}: missing value(s) for {missing}")

    genre = row["Genre"].strip().title()
    if genre not in ("Male", "Female"):
        raise ValueError(f"line {line_number}: unexpected genre {row['Genre']!r}")

    try:
        customer_id = int(row["CustomerID"])
        age = int(row["Age"])
        income = int(row["Annual Income (k$)"])
        score = int(row["Spending Score (1-100)"])
    except ValueError as exc:
        raise ValueError(f"line {line_number}: non-numeric value ({exc})") from exc

    if customer_id < 1:
        raise ValueError(f"line {line_number}: CustomerID must be positive")
    if not 1 <= age <= 120:
        raise ValueError(f"line {line_number}: age {age} out of range 1-120")
    if income < 0:
        raise ValueError(f"line {line_number}: negative income {income}")
    if not 1 <= score <= 100:
        raise ValueError(f"line {line_number}: spending score {score} out of range 1-100")

    return Customer(
        id=customer_id,
        genre=genre,
        age=age,
        annual_income_k=income,
        spending_score=score,
    )


def import_csv(csv_path: Path) -> tuple[int, list[str]]:
    """Import the CSV file; returns (imported_count, list_of_skipped_row_errors)."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    Base.metadata.create_all(bind=engine)

    imported = 0
    errors: list[str] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        expected = set(CSV_COLUMNS)
        actual = set(reader.fieldnames or [])
        if not expected.issubset(actual):
            raise ValueError(
                f"Unexpected CSV header. Missing columns: {sorted(expected - actual)}"
            )

        with SessionLocal() as session:
            for line_number, row in enumerate(reader, start=2):
                try:
                    customer = parse_row(row, line_number)
                except ValueError as exc:
                    errors.append(str(exc))
                    continue
                session.merge(customer)
                imported += 1
            session.commit()

    return imported, errors


def main() -> int:
    default_csv = Path(__file__).resolve().parent.parent / "data" / "Shopping_data.csv"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=default_csv, help="Path to the CSV file")
    args = parser.parse_args()

    imported, errors = import_csv(args.csv)
    print(f"Imported/updated {imported} customers from {args.csv}")
    if errors:
        print(f"Skipped {len(errors)} invalid row(s):")
        for error in errors:
            print(f"  - {error}")
    return 0 if imported else 1


if __name__ == "__main__":
    raise SystemExit(main())
