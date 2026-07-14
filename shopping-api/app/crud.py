"""Query logic for the customers table.

Keeping the database access here keeps the route handlers in ``main.py`` thin
and makes the querying easy to unit-test in isolation.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.orm import Session

from .models import Customer


@dataclass
class CustomerFilters:
    """Container for the optional filters accepted by the list endpoint."""

    gender: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_spending: int | None = None
    max_spending: int | None = None
    search: str | None = None


def _apply_filters(stmt: Select, filters: CustomerFilters) -> Select:
    """Attach WHERE clauses to ``stmt`` for every filter that was supplied."""
    if filters.gender is not None:
        stmt = stmt.where(Customer.gender == filters.gender)
    if filters.min_age is not None:
        stmt = stmt.where(Customer.age >= filters.min_age)
    if filters.max_age is not None:
        stmt = stmt.where(Customer.age <= filters.max_age)
    if filters.min_income is not None:
        stmt = stmt.where(Customer.annual_income >= filters.min_income)
    if filters.max_income is not None:
        stmt = stmt.where(Customer.annual_income <= filters.max_income)
    if filters.min_spending is not None:
        stmt = stmt.where(Customer.spending_score >= filters.min_spending)
    if filters.max_spending is not None:
        stmt = stmt.where(Customer.spending_score <= filters.max_spending)
    if filters.search:
        # Basic case-insensitive search across the textual fields
        # (customer_id and gender), since the dataset has no name column.
        term = f"%{filters.search.strip()}%"
        stmt = stmt.where(
            or_(Customer.customer_id.ilike(term), Customer.gender.ilike(term))
        )
    return stmt


def list_customers(
    db: Session,
    filters: CustomerFilters,
    *,
    limit: int,
    offset: int,
    sort_by: str = "customer_id",
    order: str = "asc",
) -> tuple[list[Customer], int]:
    """Return a page of customers plus the total count for the given filters."""
    base = _apply_filters(select(Customer), filters)

    # Total count of matching rows (before pagination) for the page metadata.
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    sort_column = getattr(Customer, sort_by, Customer.customer_id)
    direction = desc if order == "desc" else asc
    # Secondary sort on customer_id keeps ordering stable/deterministic.
    stmt = base.order_by(direction(sort_column), asc(Customer.customer_id))
    stmt = stmt.limit(limit).offset(offset)

    items = list(db.scalars(stmt).all())
    return items, total


def get_customer(db: Session, customer_id: str) -> Customer | None:
    """Look up a single customer by their dataset business id (e.g. "0001")."""
    return db.scalar(select(Customer).where(Customer.customer_id == customer_id))


def get_stats(db: Session) -> dict:
    """Compute aggregate statistics across the whole dataset."""
    total = db.scalar(select(func.count()).select_from(Customer)) or 0

    gender_rows = db.execute(
        select(Customer.gender, func.count()).group_by(Customer.gender)
    ).all()
    gender_breakdown = {gender: count for gender, count in gender_rows}

    def field_stats(column) -> dict:
        row = db.execute(
            select(func.min(column), func.max(column), func.avg(column))
        ).one()
        minimum, maximum, average = row
        return {
            "min": float(minimum) if minimum is not None else 0.0,
            "max": float(maximum) if maximum is not None else 0.0,
            "avg": round(float(average), 2) if average is not None else 0.0,
        }

    return {
        "total_customers": total,
        "gender_breakdown": gender_breakdown,
        "age": field_stats(Customer.age),
        "annual_income": field_stats(Customer.annual_income),
        "spending_score": field_stats(Customer.spending_score),
    }
