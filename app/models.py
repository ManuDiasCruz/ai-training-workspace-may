"""SQLAlchemy ORM models for the shopping dataset."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Customer(Base):
    """A single shopping-mall customer record."""

    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    genre: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_income_k: Mapped[int] = mapped_column(Integer, nullable=False)
    spending_score: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("age >= 0", name="ck_customer_age_non_negative"),
        CheckConstraint("annual_income_k >= 0", name="ck_customer_income_non_negative"),
        CheckConstraint(
            "spending_score BETWEEN 1 AND 100",
            name="ck_customer_spending_score_range",
        ),
        Index("ix_customers_age", "age"),
        Index("ix_customers_income", "annual_income_k"),
        Index("ix_customers_score", "spending_score"),
    )
