"""SQLAlchemy ORM models."""
from __future__ import annotations

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Customer(Base):
    """A single mall customer record.

    Mirrors the columns of ``Shopping_data.csv``:
    ``CustomerID, Genre, Age, Annual Income (k$), Spending Score (1-100)``.
    """

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("gender IN ('Male', 'Female')", name="ck_customers_gender"),
        CheckConstraint("age >= 0", name="ck_customers_age_non_negative"),
        CheckConstraint(
            "spending_score BETWEEN 1 AND 100", name="ck_customers_spending_range"
        ),
        CheckConstraint("annual_income >= 0", name="ck_customers_income_non_negative"),
    )

    # Surrogate primary key (auto-incrementing).
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business key from the dataset, e.g. "0001". Stored as text to keep the
    # zero-padding that identifies customers in the source file.
    customer_id: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, nullable=False
    )

    gender: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    age: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    # Annual income expressed in thousands of dollars (k$), as in the dataset.
    annual_income: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    # Mall-assigned spending score, 1-100.
    spending_score: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<Customer {self.customer_id} {self.gender} age={self.age} "
            f"income={self.annual_income}k score={self.spending_score}>"
        )
