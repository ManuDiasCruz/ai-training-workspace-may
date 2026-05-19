"""Import the shopping CSV into the local SQLite database.

The importer normalizes header names (snake_case, strips units like
"(USD)") so it accepts the original Kaggle "Customer Shopping Trends"
column names as well as the snake_case sample produced by the
generator script. Missing optional columns fall back to safe defaults.

Run as: python -m app.import_data
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import delete

from .config import CSV_PATH
from .db import Base, SessionLocal, engine
from .models import Purchase

COLUMN_ALIASES = {
    "customer_id": {"customer id", "customerid"},
    "age": set(),
    "gender": set(),
    "item_purchased": {"item purchased"},
    "category": set(),
    "purchase_amount_usd": {"purchase amount (usd)", "purchase amount usd", "purchase amount"},
    "location": set(),
    "size": set(),
    "color": set(),
    "season": set(),
    "review_rating": {"review rating"},
    "subscription_status": {"subscription status"},
    "payment_method": {"payment method"},
    "shipping_type": {"shipping type"},
    "discount_applied": {"discount applied"},
    "promo_code_used": {"promo code used"},
    "previous_purchases": {"previous purchases"},
    "frequency_of_purchases": {"frequency of purchases"},
}


def _normalize(name: str) -> str:
    n = name.strip().lower()
    n = re.sub(r"\(.*?\)", "", n).strip()
    n = re.sub(r"[^a-z0-9]+", "_", n).strip("_")
    return n


def _build_header_map(fieldnames: Iterable[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        norm = _normalize(raw)
        for canonical, aliases in COLUMN_ALIASES.items():
            alias_norms = {_normalize(a) for a in aliases} | {canonical}
            if norm in alias_norms:
                mapping[canonical] = raw
                break
    return mapping


def _coerce(value: Any, kind: type, default: Any) -> Any:
    if value is None or value == "":
        return default
    try:
        return kind(value)
    except (TypeError, ValueError):
        return default


def _row_to_purchase(row: dict[str, str], hmap: dict[str, str]) -> Purchase:
    def s(field: str, default: str = "") -> str:
        col = hmap.get(field)
        return (row.get(col, default) if col else default) or default

    return Purchase(
        customer_id=_coerce(s("customer_id"), int, 0),
        age=_coerce(s("age"), int, 0),
        gender=s("gender", "Unknown"),
        item_purchased=s("item_purchased", "Unknown"),
        category=s("category", "Unknown"),
        purchase_amount_usd=_coerce(s("purchase_amount_usd"), float, 0.0),
        location=s("location", "Unknown"),
        size=s("size", ""),
        color=s("color", ""),
        season=s("season", ""),
        review_rating=_coerce(s("review_rating"), float, 0.0),
        subscription_status=s("subscription_status", "No"),
        payment_method=s("payment_method", ""),
        shipping_type=s("shipping_type", ""),
        discount_applied=s("discount_applied", "No"),
        promo_code_used=s("promo_code_used", "No"),
        previous_purchases=_coerce(s("previous_purchases"), int, 0),
        frequency_of_purchases=s("frequency_of_purchases", ""),
    )


def import_csv(csv_path: Path = CSV_PATH, *, truncate: bool = True) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at {csv_path}")

    Base.metadata.create_all(engine)
    inserted = 0
    with SessionLocal() as session:
        if truncate:
            session.execute(delete(Purchase))
        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV has no header row")
            hmap = _build_header_map(reader.fieldnames)
            batch: list[Purchase] = []
            for row in reader:
                batch.append(_row_to_purchase(row, hmap))
                if len(batch) >= 500:
                    session.add_all(batch)
                    inserted += len(batch)
                    batch = []
            if batch:
                session.add_all(batch)
                inserted += len(batch)
        session.commit()
    return inserted


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PATH
    n = import_csv(path)
    print(f"Imported {n} rows from {path}")
