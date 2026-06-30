"""Data-access helpers: querying, filtering, pagination and aggregation."""

from typing import Optional

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session

from . import models


def _apply_filters(
    stmt,
    *,
    genre: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_income: Optional[int] = None,
    max_income: Optional[int] = None,
    min_spending_score: Optional[int] = None,
    max_spending_score: Optional[int] = None,
    search: Optional[str] = None,
):
    """Apply the shared set of filters to a select statement."""
    c = models.Customer

    if genre is not None:
        # Case-insensitive match so "male"/"MALE" both work.
        stmt = stmt.where(func.lower(c.genre) == genre.lower())
    if min_age is not None:
        stmt = stmt.where(c.age >= min_age)
    if max_age is not None:
        stmt = stmt.where(c.age <= max_age)
    if min_income is not None:
        stmt = stmt.where(c.annual_income_k >= min_income)
    if max_income is not None:
        stmt = stmt.where(c.annual_income_k <= max_income)
    if min_spending_score is not None:
        stmt = stmt.where(c.spending_score >= min_spending_score)
    if max_spending_score is not None:
        stmt = stmt.where(c.spending_score <= max_spending_score)

    if search:
        # Lightweight search across textual / id fields. The dataset has no
        # free-text columns, so we match against genre and the customer id.
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(c.genre).like(term),
                cast(c.customer_id, String).like(term),
            )
        )
    return stmt


def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.get(models.Customer, customer_id)


def list_customers(
    db: Session,
    *,
    limit: int,
    offset: int,
    sort_by: str = "customer_id",
    order: str = "asc",
    **filters,
):
    """Return (total, items) for the given filters and pagination window."""
    c = models.Customer
    base = _apply_filters(select(c), **filters)

    total = db.scalar(select(func.count()).select_from(base.subquery()))

    sortable = {
        "customer_id": c.customer_id,
        "age": c.age,
        "annual_income_k": c.annual_income_k,
        "spending_score": c.spending_score,
    }
    sort_col = sortable.get(sort_by, c.customer_id)
    sort_col = sort_col.desc() if order.lower() == "desc" else sort_col.asc()

    items = list(
        db.scalars(base.order_by(sort_col).limit(limit).offset(offset)).all()
    )
    return total, items


def get_stats(db: Session, **filters) -> dict:
    """Compute aggregate statistics across the filtered dataset."""
    c = models.Customer
    base = _apply_filters(select(c), **filters).subquery()

    male = case((func.lower(base.c.genre) == "male", 1), else_=0)
    female = case((func.lower(base.c.genre) == "female", 1), else_=0)
    row = db.execute(
        select(
            func.count(),
            func.coalesce(func.sum(male), 0),
            func.coalesce(func.sum(female), 0),
            func.coalesce(func.avg(base.c.age), 0.0),
            func.coalesce(func.avg(base.c.annual_income_k), 0.0),
            func.coalesce(func.avg(base.c.spending_score), 0.0),
            func.coalesce(func.min(base.c.annual_income_k), 0),
            func.coalesce(func.max(base.c.annual_income_k), 0),
        )
    ).one()

    return {
        "total_customers": row[0],
        "male_count": int(row[1]),
        "female_count": int(row[2]),
        "avg_age": round(float(row[3]), 2),
        "avg_annual_income_k": round(float(row[4]), 2),
        "avg_spending_score": round(float(row[5]), 2),
        "min_annual_income_k": int(row[6]),
        "max_annual_income_k": int(row[7]),
    }
