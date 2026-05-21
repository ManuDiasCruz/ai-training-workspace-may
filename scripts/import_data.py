"""Import the shopping CSV into the local database with dataset validation."""

import csv
import os
import sys
from pathlib import Path

# Allow running as a script.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Customer  # noqa: E402


DEFAULT_CSV = ROOT / "data" / "Shopping_data.csv"
EXPECTED_HEADERS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]


def _validate_headers(fieldnames: list[str] | None) -> None:
    if fieldnames != EXPECTED_HEADERS:
        raise ValueError(
            "CSV headers must match: " + ", ".join(EXPECTED_HEADERS)
        )


def _parse_int(value: str, field_name: str, row_number: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"row {row_number}: {field_name} must be an integer"
        ) from exc


def _parse_customer(row: dict[str, str], row_number: int) -> Customer:
    code = (row.get("CustomerID") or "").strip()
    if not code:
        raise ValueError(f"row {row_number}: CustomerID is required")

    gender = (row.get("Genre") or "").strip()
    if gender not in {"Male", "Female"}:
        raise ValueError(f"row {row_number}: Genre must be Male or Female")

    age = _parse_int(row["Age"], "Age", row_number)
    income = _parse_int(row["Annual Income (k$)"], "Annual Income (k$)", row_number)
    score = _parse_int(
        row["Spending Score (1-100)"],
        "Spending Score (1-100)",
        row_number,
    )

    if not 0 <= age <= 130:
        raise ValueError(f"row {row_number}: Age must be between 0 and 130")
    if income < 0:
        raise ValueError(f"row {row_number}: Annual Income (k$) must be >= 0")
    if not 1 <= score <= 100:
        raise ValueError(
            f"row {row_number}: Spending Score (1-100) must be between 1 and 100"
        )

    return Customer(
        customer_code=code,
        gender=gender,
        age=age,
        annual_income_k=income,
        spending_score=score,
    )


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
            _validate_headers(reader.fieldnames)
            for row_number, row in enumerate(reader, start=2):
                customer = _parse_customer(row, row_number)
                if customer.customer_code in existing:
                    continue
                session.add(customer)
                existing.add(customer.customer_code)
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
    database_url = os.environ.get("DATABASE_URL", "sqlite:///shopping.db")
    print(f"Importing {csv_path} into {database_url}")
    n = import_csv(csv_path)
    print(f"Inserted {n} new customers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
