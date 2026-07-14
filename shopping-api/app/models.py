"""ORM model for the shopping (mall customers) dataset.

Source CSV columns -> model fields:
    CustomerID              -> customer_id   (kept as text to preserve "0001" padding)
    Genre                   -> gender        (renamed for clarity; values Male/Female)
    Age                     -> age
    Annual Income (k$)      -> annual_income_k
    Spending Score (1-100)  -> spending_score
"""
from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    # The dataset ships zero-padded 4-digit ids ("0001"); store as TEXT so the
    # padding is preserved and the natural key stays stable.
    customer_id: Mapped[str] = mapped_column(String, primary_key=True)
    gender: Mapped[str] = mapped_column(String, nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    annual_income_k: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    spending_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("gender IN ('Male', 'Female')", name="ck_customers_gender"),
        CheckConstraint("age >= 0 AND age <= 120", name="ck_customers_age"),
        CheckConstraint("annual_income_k >= 0", name="ck_customers_income"),
        CheckConstraint(
            "spending_score >= 1 AND spending_score <= 100",
            name="ck_customers_spending_score",
        ),
        Index("ix_customers_income_score", "annual_income_k", "spending_score"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"Customer(customer_id={self.customer_id!r}, gender={self.gender!r}, "
            f"age={self.age}, annual_income_k={self.annual_income_k}, "
            f"spending_score={self.spending_score})"
        )
