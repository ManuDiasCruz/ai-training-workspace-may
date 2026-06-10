"""SQLAlchemy ORM models for the shopping dataset."""
from __future__ import annotations

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    """A single shopping-mall customer record.

    The raw CSV columns are normalised onto clean, queryable attributes:

    =========================  ==================
    CSV column                 Model attribute
    =========================  ==================
    CustomerID                 customer_id (PK)
    Genre                      gender
    Age                        age
    Annual Income (k$)         annual_income_k
    Spending Score (1-100)     spending_score
    =========================  ==================
    """

    __tablename__ = "customers"

    # CustomerID is a stable identifier in the source data, so it is used as the
    # primary key directly (leading zeros are dropped when cast to INTEGER).
    customer_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_income_k: Mapped[int] = mapped_column(Integer, nullable=False)
    spending_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Indexes on every filterable column keep range/equality queries efficient.
    __table_args__ = (
        Index("ix_customers_gender", "gender"),
        Index("ix_customers_age", "age"),
        Index("ix_customers_annual_income_k", "annual_income_k"),
        Index("ix_customers_spending_score", "spending_score"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<Customer id={self.customer_id} gender={self.gender!r} "
            f"age={self.age} income={self.annual_income_k}k "
            f"score={self.spending_score}>"
        )
