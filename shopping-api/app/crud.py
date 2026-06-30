"""Query helpers (CRUD) for the customers table.

All read operations accept the same set of optional filters so that listing,
filtering and search share a single, well-tested query builder.
"""
from typing import Optional, Tuple

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Query, Session

from . import models


def _apply_filters(
    query: Query,
    *,
    genre: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_income: Optional[int] = None,
    max_income: Optional[int] = None,
    min_spending_score: Optional[int] = None,
    max_spending_score: Optional[int] = None,
    search: Optional[str] = None,
) -> Query:
    """Apply optional filtering / search clauses to a customers query."""
    if genre is not None:
        query = query.filter(models.Customer.genre == genre)
    if min_age is not None:
        query = query.filter(models.Customer.age >= min_age)
    if max_age is not None:
        query = query.filter(models.Customer.age <= max_age)
    if min_income is not None:
        query = query.filter(models.Customer.annual_income >= min_income)
    if max_income is not None:
        query = query.filter(models.Customer.annual_income <= max_income)
    if min_spending_score is not None:
        query = query.filter(models.Customer.spending_score >= min_spending_score)
    if max_spending_score is not None:
        query = query.filter(models.Customer.spending_score <= max_spending_score)
    if search:
        term = f"%{search.strip()}%"
        # Free-text search across id, genre and the numeric columns (cast to
        # text) so a query like "19" matches a customer id, age, income or score.
        query = query.filter(
            or_(
                models.Customer.customer_id.ilike(term),
                models.Customer.genre.ilike(term),
                cast(models.Customer.age, String).ilike(term),
                cast(models.Customer.annual_income, String).ilike(term),
                cast(models.Customer.spending_score, String).ilike(term),
            )
        )
    return query


# Whitelist of columns that may be used for ordering, to avoid SQL injection
# via the ``sort_by`` query parameter.
SORTABLE_FIELDS = {
    "customer_id": models.Customer.customer_id,
    "age": models.Customer.age,
    "annual_income": models.Customer.annual_income,
    "spending_score": models.Customer.spending_score,
}


def list_customers(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "customer_id",
    order: str = "asc",
    **filters,
) -> Tuple[int, list]:
    """Return ``(total, items)`` for the given filters and pagination."""
    base = _apply_filters(db.query(models.Customer), **filters)
    total = base.order_by(None).count()

    sort_col = SORTABLE_FIELDS.get(sort_by, models.Customer.customer_id)
    sort_col = sort_col.desc() if order == "desc" else sort_col.asc()

    items = base.order_by(sort_col).offset(offset).limit(limit).all()
    return total, items


def get_customer(db: Session, customer_id: str) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id
    ).first()


def stats(db: Session, **filters) -> dict:
    """Aggregate statistics over the filtered dataset."""
    base = _apply_filters(db.query(models.Customer), **filters)
    total = base.count()

    agg = base.with_entities(
        func.avg(models.Customer.age),
        func.avg(models.Customer.annual_income),
        func.avg(models.Customer.spending_score),
    ).one()

    breakdown = dict(
        base.with_entities(
            models.Customer.genre, func.count(models.Customer.customer_id)
        ).group_by(models.Customer.genre).all()
    )

    def _round(value):
        return round(value, 2) if value is not None else None

    return {
        "total": total,
        "avg_age": _round(agg[0]),
        "avg_annual_income": _round(agg[1]),
        "avg_spending_score": _round(agg[2]),
        "genre_breakdown": breakdown,
    }
