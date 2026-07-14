"""CSV -> SQLite import logic.

Kept separate from the CLI wrapper (``scripts/import_data.py``) so it can be
reused for optional first-boot seeding inside the API.
"""
from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Customer

# CSV header -> model attribute mapping.
_COLUMN_MAP = {
    "CustomerID": "customer_id",
    "Genre": "gender",
    "Age": "age",
    "Annual Income (k$)": "annual_income_k",
    "Spending Score (1-100)": "spending_score",
}

_VALID_GENDERS = {"Male", "Female"}


class DatasetError(ValueError):
    """Raised when the CSV cannot be parsed into valid customer rows."""


def _parse_row(row: dict[str, str], line_no: int) -> Customer:
    """Validate and convert a single CSV row into a ``Customer`` instance."""
    missing = [col for col in _COLUMN_MAP if col not in row]
    if missing:
        raise DatasetError(f"line {line_no}: missing columns {missing}")

    customer_id = (row["CustomerID"] or "").strip()
    gender = (row["Genre"] or "").strip()
    if not customer_id:
        raise DatasetError(f"line {line_no}: empty CustomerID")
    if gender not in _VALID_GENDERS:
        raise DatasetError(f"line {line_no}: unexpected gender {gender!r}")

    try:
        age = int(row["Age"])
        annual_income_k = int(row["Annual Income (k$)"])
        spending_score = int(row["Spending Score (1-100)"])
    except (TypeError, ValueError) as exc:
        raise DatasetError(f"line {line_no}: non-integer numeric field ({exc})") from exc

    if not 0 <= age <= 120:
        raise DatasetError(f"line {line_no}: age {age} out of range 0-120")
    if annual_income_k < 0:
        raise DatasetError(f"line {line_no}: negative income {annual_income_k}")
    if not 1 <= spending_score <= 100:
        raise DatasetError(f"line {line_no}: spending score {spending_score} out of range 1-100")

    return Customer(
        customer_id=customer_id,
        gender=gender,
        age=age,
        annual_income_k=annual_income_k,
        spending_score=spending_score,
    )


def import_csv(db: Session, csv_path: str | Path, *, replace: bool = True) -> int:
    """Load ``csv_path`` into the customers table.

    Args:
        db: an open SQLAlchemy session.
        csv_path: path to the source CSV.
        replace: when True (default) the table is cleared first, making the
            import idempotent — re-running always yields exactly the CSV.

    Returns:
        The number of rows imported.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise DatasetError(f"CSV not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        customers = [_parse_row(row, i) for i, row in enumerate(reader, start=2)]

    if not customers:
        raise DatasetError("CSV contained no data rows")

    seen: set[str] = set()
    for c in customers:
        if c.customer_id in seen:
            raise DatasetError(f"duplicate CustomerID {c.customer_id!r} in CSV")
        seen.add(c.customer_id)

    if replace:
        db.query(Customer).delete()
    db.add_all(customers)
    db.commit()
    return len(customers)


def seed_if_empty(db: Session, csv_path: str | Path) -> int:
    """Import the CSV only when the table is empty. Returns rows imported (0 if skipped)."""
    existing = db.scalar(select(func.count()).select_from(Customer)) or 0
    if existing:
        return 0
    return import_csv(db, csv_path, replace=False)
