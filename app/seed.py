"""Load and persist the shopping dataset into the database."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.models import Customer

# Columns the importer expects to find in the source CSV.
REQUIRED_COLUMNS = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]


def _parse_rows(csv_path: Path) -> Iterator[Customer]:
    """Yield ``Customer`` instances parsed from the CSV, validating each row."""
    # utf-8-sig transparently strips a BOM if one is present; newline="" lets
    # the csv module handle the file's CRLF line endings correctly.
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        missing = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing:
            raise ValueError(
                f"Dataset {csv_path} is missing required columns {missing}; "
                f"found {headers}."
            )

        for line_no, row in enumerate(reader, start=2):  # line 1 is the header
            try:
                yield Customer(
                    customer_id=int(row["CustomerID"]),
                    gender=row["Genre"].strip(),
                    age=int(row["Age"]),
                    annual_income_k=int(row["Annual Income (k$)"]),
                    spending_score=int(row["Spending Score (1-100)"]),
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid record on line {line_no} of {csv_path}: {row} ({exc})"
                ) from exc


def seed_database(
    session: Session,
    csv_path: str | Path | None = None,
    *,
    replace: bool = True,
) -> int:
    """Populate the ``customers`` table from the CSV.

    Args:
        session: An open SQLAlchemy session.
        csv_path: Path to the dataset CSV (defaults to the bundled dataset).
        replace: When True (default), existing rows are deleted first so the
            import is idempotent.

    Returns:
        The number of records inserted.
    """
    csv_path = Path(csv_path) if csv_path else config.DATASET_PATH
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    if replace:
        session.query(Customer).delete()

    customers = list(_parse_rows(csv_path))
    session.add_all(customers)
    session.commit()
    return len(customers)


def count_customers(session: Session) -> int:
    """Return the number of customer rows currently persisted."""
    return session.scalar(select(func.count()).select_from(Customer)) or 0
