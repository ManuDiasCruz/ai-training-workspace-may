"""CRUD and query helpers for the customers table."""

from __future__ import annotations

from typing import Literal

from sqlalchemy import String, func, or_, select
from sqlalchemy.orm import Session

from app.models import Customer
from app.schemas import CustomerCreate, CustomerUpdate


SortField = Literal["customer_id", "age", "annual_income_k", "spending_score"]
SortOrder = Literal["asc", "desc"]


def list_customers(
    db: Session,
    *,
    limit: int,
    offset: int,
    genre: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_income: int | None = None,
    max_income: int | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    search: str | None = None,
    sort_by: SortField = "customer_id",
    sort_order: SortOrder = "asc",
) -> tuple[list[Customer], int]:
    stmt = select(Customer)

    if genre:
        stmt = stmt.where(func.lower(Customer.genre) == genre.lower())
    if min_age is not None:
        stmt = stmt.where(Customer.age >= min_age)
    if max_age is not None:
        stmt = stmt.where(Customer.age <= max_age)
    if min_income is not None:
        stmt = stmt.where(Customer.annual_income_k >= min_income)
    if max_income is not None:
        stmt = stmt.where(Customer.annual_income_k <= max_income)
    if min_score is not None:
        stmt = stmt.where(Customer.spending_score >= min_score)
    if max_score is not None:
        stmt = stmt.where(Customer.spending_score <= max_score)

    if search:
        needle = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Customer.genre).like(needle),
                func.cast(Customer.customer_id, String).like(needle),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    sort_column = {
        "customer_id": Customer.customer_id,
        "age": Customer.age,
        "annual_income_k": Customer.annual_income_k,
        "spending_score": Customer.spending_score,
    }[sort_by]
    stmt = stmt.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
    stmt = stmt.limit(limit).offset(offset)

    items = list(db.scalars(stmt).all())
    return items, total


def get_customer(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    customer_id = payload.customer_id
    if customer_id is None:
        max_id = db.scalar(select(func.max(Customer.customer_id))) or 0
        customer_id = max_id + 1

    if db.get(Customer, customer_id) is not None:
        raise ValueError(f"customer_id {customer_id} already exists")

    customer = Customer(
        customer_id=customer_id,
        genre=payload.genre,
        age=payload.age,
        annual_income_k=payload.annual_income_k,
        spending_score=payload.spending_score,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(
    db: Session, customer_id: int, payload: CustomerUpdate
) -> Customer | None:
    customer = db.get(Customer, customer_id)
    if customer is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> bool:
    customer = db.get(Customer, customer_id)
    if customer is None:
        return False
    db.delete(customer)
    db.commit()
    return True


def stats(db: Session) -> dict:
    total = db.scalar(select(func.count(Customer.customer_id))) or 0

    by_genre_rows = db.execute(
        select(Customer.genre, func.count(Customer.customer_id)).group_by(Customer.genre)
    ).all()
    by_genre = {row[0]: row[1] for row in by_genre_rows}

    def _agg(column) -> dict[str, float]:
        row = db.execute(
            select(func.min(column), func.max(column), func.avg(column))
        ).one()
        return {
            "min": float(row[0]) if row[0] is not None else 0.0,
            "max": float(row[1]) if row[1] is not None else 0.0,
            "avg": round(float(row[2]), 2) if row[2] is not None else 0.0,
        }

    return {
        "total": total,
        "by_genre": by_genre,
        "age": _agg(Customer.age),
        "annual_income_k": _agg(Customer.annual_income_k),
        "spending_score": _agg(Customer.spending_score),
    }
