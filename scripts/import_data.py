"""Import the Shopping_data.csv dataset into the local SQLite database.

Usage:
    python -m scripts.import_data [path/to/Shopping_data.csv]

Re-running is safe: existing rows (matched by customer_code) are skipped.
"""
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
REQUIRED_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}


def parse_row(row: dict[str, str], line_number: int) -> dict[str, object]:
    """Validate and convert one source row into the database field format."""
    try:
        code = row["CustomerID"].strip()
        gender = row["Genre"].strip()
        age = int(row["Age"])
        income = int(row["Annual Income (k$)"])
        score = int(row["Spending Score (1-100)"])
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid row at CSV line {line_number}: {exc}") from exc

    if not code or len(code) > 8:
        raise ValueError(f"Invalid CustomerID at CSV line {line_number}: {code!r}")
    if gender not in {"Male", "Female"}:
        raise ValueError(f"Invalid Genre at CSV line {line_number}: {gender!r}")
    if not 0 <= age <= 130:
        raise ValueError(f"Invalid Age at CSV line {line_number}: {age}")
    if income < 0:
        raise ValueError(
            f"Invalid Annual Income (k$) at CSV line {line_number}: {income}"
        )
    if not 1 <= score <= 100:
        raise ValueError(
            f"Invalid Spending Score (1-100) at CSV line {line_number}: {score}"
        )

    return {
        "customer_code": code,
        "gender": gender,
        "age": age,
        "annual_income_k": income,
        "spending_score": score,
    }


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
            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing_columns:
                raise ValueError(
                    "Dataset is missing required columns: "
                    + ", ".join(sorted(missing_columns))
                )

            for line_number, row in enumerate(reader, start=2):
                values = parse_row(row, line_number)
                code = values["customer_code"]
                if code in existing:
                    continue
                session.add(Customer(**values))
                existing.add(code)
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
