"""Read-only query helpers used by the API layer.

This module knows about the database/ORM only; it returns ORM objects or plain
dictionaries and never depends on the HTTP/Pydantic layer.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Customer


@dataclass
class CustomerFilters:
    """Filter criteria for customer queries (all optional)."""

    gender: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    search: str | None = None


def _build_conditions(f: CustomerFilters) -> list:
    """Translate filter criteria into a list of SQLAlchemy WHERE clauses."""
    conditions: list = []
    if f.gender is not None:
        conditions.append(Customer.gender == f.gender)
    if f.min_age is not None:
        conditions.append(Customer.age >= f.min_age)
    if f.max_age is not None:
        conditions.append(Customer.age <= f.max_age)
    if f.min_income is not None:
        conditions.append(Customer.annual_income_k >= f.min_income)
    if f.max_income is not None:
        conditions.append(Customer.annual_income_k <= f.max_income)
    if f.min_spending_score is not None:
        conditions.append(Customer.spending_score >= f.min_spending_score)
    if f.max_spending_score is not None:
        conditions.append(Customer.spending_score <= f.max_spending_score)
    if f.search:
        # Basic search: case-insensitive match on gender, plus an exact match
        # on customer_id when the term is numeric. (The dataset has no free-text
        # columns, so search is intentionally scoped to these fields.)
        term = f.search.strip()
        search_clauses = [func.lower(Customer.gender) == term.lower()]
        if term.isdigit():
            search_clauses.append(Customer.customer_id == int(term))
        conditions.append(or_(*search_clauses))
    return conditions


def list_customers(
    db: Session,
    filters: CustomerFilters,
    *,
    page: int,
    page_size: int,
    sort_by: str = "customer_id",
    order: str = "asc",
) -> tuple[list[Customer], int]:
    """Return a page of customers matching ``filters`` plus the total count."""
    conditions = _build_conditions(filters)

    count_stmt = select(func.count()).select_from(Customer)
    data_stmt = select(Customer)
    if conditions:
        count_stmt = count_stmt.where(*conditions)
        data_stmt = data_stmt.where(*conditions)

    total = db.scalar(count_stmt) or 0

    sort_column = getattr(Customer, sort_by, Customer.customer_id)
    sort_column = sort_column.desc() if order == "desc" else sort_column.asc()
    data_stmt = (
        data_stmt.order_by(sort_column)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(data_stmt).all())
    return items, total


def get_customer(db: Session, customer_id: int) -> Customer | None:
    """Return a single customer by primary key, or None if it does not exist."""
    return db.get(Customer, customer_id)


def count_customers(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Customer)) or 0


def get_stats(db: Session, filters: CustomerFilters) -> dict[str, Any]:
    """Compute aggregate statistics over the (optionally filtered) customer set."""
    conditions = _build_conditions(filters)

    agg_stmt = select(
        func.count(),
        func.min(Customer.age),
        func.max(Customer.age),
        func.avg(Customer.age),
        func.min(Customer.annual_income_k),
        func.max(Customer.annual_income_k),
        func.avg(Customer.annual_income_k),
        func.min(Customer.spending_score),
        func.max(Customer.spending_score),
        func.avg(Customer.spending_score),
    ).select_from(Customer)
    gender_stmt = select(Customer.gender, func.count()).select_from(Customer)
    if conditions:
        agg_stmt = agg_stmt.where(*conditions)
        gender_stmt = gender_stmt.where(*conditions)
    gender_stmt = gender_stmt.group_by(Customer.gender)

    row = db.execute(agg_stmt).one()
    gender_rows = db.execute(gender_stmt).all()

    def _stat(minimum: Any, maximum: Any, average: Any) -> dict[str, Any]:
        return {
            "min": minimum,
            "max": maximum,
            "average": round(average, 2) if average is not None else None,
        }

    return {
        "total_customers": row[0],
        # Always expose both genders for a stable response shape.
        "gender_distribution": {"Male": 0, "Female": 0, **dict(gender_rows)},
        "age": _stat(row[1], row[2], row[3]),
        "annual_income_k": _stat(row[4], row[5], row[6]),
        "spending_score": _stat(row[7], row[8], row[9]),
        "filters_applied": {k: v for k, v in asdict(filters).items() if v is not None},
    }
