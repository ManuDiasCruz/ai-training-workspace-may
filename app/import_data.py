"""Import the Drive shopping CSV into the local database.

Run as:
    python -m app.import_data
    python -m app.import_data path/to/Shopping_data.csv
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete

from .config import CSV_PATH
from .db import Base, SessionLocal, engine
from .models import Customer
from .search_index import ensure_search_index

COLUMN_ALIASES = {
    "customer_id": {"customerid", "customer id"},
    "genre": {"genre", "gender"},
    "age": {"age"},
    "annual_income_k": {"annual income (k$)", "annual income k", "annual income"},
    "spending_score": {"spending score (1-100)", "spending score"},
}

REQUIRED_COLUMNS = set(COLUMN_ALIASES)
VALID_GENRES = {"Female", "Male"}


def _normalize(name: str) -> str:
    n = name.strip().lower()
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return " ".join(n.split())


def _build_header_map(fieldnames: Iterable[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        norm = _normalize(raw)
        for canonical, aliases in COLUMN_ALIASES.items():
            if norm in {_normalize(alias) for alias in aliases} | {_normalize(canonical)}:
                mapping[canonical] = raw
                break
    missing = sorted(REQUIRED_COLUMNS - set(mapping))
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(missing)}")
    return mapping


def _int(value: str, field: str, row_number: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer for {field} on CSV row {row_number}") from exc


def _require(value: str, field: str, row_number: int) -> str:
    if not value:
        raise ValueError(f"Missing value for {field} on CSV row {row_number}")
    return value


def _validate_range(value: int, field: str, row_number: int, *, low: int, high: int) -> int:
    if not low <= value <= high:
        raise ValueError(f"{field} on CSV row {row_number} must be between {low} and {high}")
    return value


def _row_to_customer(row: dict[str, str], hmap: dict[str, str], row_number: int) -> Customer:
    def value(field: str) -> str:
        return (row.get(hmap[field]) or "").strip()

    customer_id = _require(value("customer_id"), "customer_id", row_number)
    genre = _require(value("genre"), "genre", row_number)
    if genre not in VALID_GENRES:
        raise ValueError(f"Invalid genre on CSV row {row_number}: {genre}")

    age = _validate_range(_int(value("age"), "age", row_number), "age", row_number, low=0, high=120)
    annual_income_k = _validate_range(
        _int(value("annual_income_k"), "annual_income_k", row_number),
        "annual_income_k",
        row_number,
        low=0,
        high=1_000,
    )
    spending_score = _validate_range(
        _int(value("spending_score"), "spending_score", row_number),
        "spending_score",
        row_number,
        low=1,
        high=100,
    )

    return Customer(
        customer_id=customer_id,
        genre=genre,
        age=age,
        annual_income_k=annual_income_k,
        spending_score=spending_score,
    )


def import_csv(csv_path: Path = CSV_PATH, *, truncate: bool = True) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at {csv_path}")

    Base.metadata.create_all(engine)
    ensure_search_index(engine)
    inserted = 0
    with SessionLocal() as session:
        if truncate:
            session.execute(delete(Customer))
        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV has no header row")
            hmap = _build_header_map(reader.fieldnames)
            batch = [
                _row_to_customer(row, hmap, row_number)
                for row_number, row in enumerate(reader, start=2)
            ]
            session.add_all(batch)
            inserted = len(batch)
        session.commit()
    ensure_search_index(engine, rebuild=True)
    return inserted


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PATH
    n = import_csv(path)
    print(f"Imported {n} rows from {path}")
