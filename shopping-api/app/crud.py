"""Query logic for the customers table (filtering, search, pagination, stats)."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from .models import Customer
from .schemas import SortField, SortOrder


@dataclass
class CustomerFilters:
    """Validated filter/search/sort/pagination parameters for a list query."""

    page: int = 1
    page_size: int = 20
    gender: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    search: str | None = None
    sort_by: SortField = SortField.customer_id
    order: SortOrder = SortOrder.asc


def _apply_filters(stmt, f: CustomerFilters):
    """Attach WHERE clauses for every provided filter to a select statement."""
    if f.gender is not None:
        # Case-insensitive exact match so "male" and "Male" both work.
        stmt = stmt.where(func.lower(Customer.gender) == f.gender.lower())
    if f.min_age is not None:
        stmt = stmt.where(Customer.age >= f.min_age)
    if f.max_age is not None:
        stmt = stmt.where(Customer.age <= f.max_age)
    if f.min_income is not None:
        stmt = stmt.where(Customer.annual_income_k >= f.min_income)
    if f.max_income is not None:
        stmt = stmt.where(Customer.annual_income_k <= f.max_income)
    if f.min_spending_score is not None:
        stmt = stmt.where(Customer.spending_score >= f.min_spending_score)
    if f.max_spending_score is not None:
        stmt = stmt.where(Customer.spending_score <= f.max_spending_score)
    if f.search:
        # The dataset has no free-text field, so "search" matches the id or
        # gender substrings (case-insensitive).
        term = f"%{f.search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Customer.customer_id).like(term),
                func.lower(Customer.gender).like(term),
            )
        )
    return stmt


def count_customers(db: Session, f: CustomerFilters) -> int:
    """Total number of records matching the filters (ignoring pagination)."""
    stmt = _apply_filters(select(func.count()).select_from(Customer), f)
    return db.scalar(stmt) or 0


def list_customers(db: Session, f: CustomerFilters) -> list[Customer]:
    """Return one page of filtered, sorted customer records."""
    stmt = _apply_filters(select(Customer), f)

    sort_column = getattr(Customer, f.sort_by.value)
    direction = desc if f.order is SortOrder.desc else asc
    # Secondary sort on the primary key gives a stable, deterministic order.
    stmt = stmt.order_by(direction(sort_column), asc(Customer.customer_id))

    offset = (f.page - 1) * f.page_size
    stmt = stmt.offset(offset).limit(f.page_size)
    return list(db.scalars(stmt).all())


def get_customer(db: Session, customer_id: str) -> Customer | None:
    """Fetch a single customer by primary key, or ``None`` if absent."""
    return db.get(Customer, customer_id)


def _metric(db: Session, column) -> dict:
    row = db.execute(
        select(func.min(column), func.max(column), func.avg(column))
    ).one()
    mn, mx, avg = row
    return {
        "min": float(mn) if mn is not None else None,
        "max": float(mx) if mx is not None else None,
        "avg": round(float(avg), 2) if avg is not None else None,
    }


def get_stats(db: Session) -> dict:
    """Compute aggregate statistics across the whole dataset."""
    total = db.scalar(select(func.count()).select_from(Customer)) or 0

    gender_rows = db.execute(
        select(Customer.gender, func.count())
        .group_by(Customer.gender)
        .order_by(Customer.gender)
    ).all()

    return {
        "total_customers": total,
        "by_gender": [{"gender": g, "count": c} for g, c in gender_rows],
        "age": _metric(db, Customer.age),
        "annual_income_k": _metric(db, Customer.annual_income_k),
        "spending_score": _metric(db, Customer.spending_score),
    }
