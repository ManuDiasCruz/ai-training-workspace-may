"""Import the Shopping_data.csv dataset into the local SQLite database.

Usage:
    python -m scripts.import_data [path/to/Shopping_data.csv]

Re-running is safe: existing rows (matched by customer_code) are skipped.
"""
import csv
import os
import sys
from pathlib import Path

from pydantic import ValidationError

# Allow running as a script.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Customer  # noqa: E402
from app.schemas import CustomerCreate  # noqa: E402


DEFAULT_CSV = ROOT / "data" / "Shopping_data.csv"
REQUIRED_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}


def parse_row(row: dict, line_number: int) -> CustomerCreate:
    """Normalize and validate one CSV row before it reaches the database."""
    try:
        return CustomerCreate(
            customer_code=(row.get("CustomerID") or "").strip(),
            gender=(row.get("Genre") or "").strip(),
            age=int(row["Age"]),
            annual_income_k=int(row["Annual Income (k$)"]),
            spending_score=int(row["Spending Score (1-100)"]),
        )
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise ValueError(f"Invalid data at CSV line {line_number}: {exc}") from exc


def import_csv(csv_path: Path) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    try:
        existing = {c[0] for c in session.query(Customer.customer_code).all()}
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            actual_columns = set(reader.fieldnames or [])
            missing_columns = sorted(REQUIRED_COLUMNS - actual_columns)
            if missing_columns:
                raise ValueError(
                    "Dataset is missing required columns: " + ", ".join(missing_columns)
                )

            for line_number, row in enumerate(reader, start=2):
                payload = parse_row(row, line_number)
                if payload.customer_code in existing:
                    continue
                customer = Customer(**payload.model_dump())
                session.add(customer)
                existing.add(payload.customer_code)
                inserted += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return inserted


def main() -> int:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    print(f"Importing {csv_path} into {os.environ.get('DATABASE_URL', 'sqlite:///shopping.db')}")
    n = import_csv(csv_path)
    print(f"Inserted {n} new customers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
