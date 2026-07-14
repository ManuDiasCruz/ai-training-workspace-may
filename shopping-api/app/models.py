"""SQLAlchemy ORM models."""

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Customer(Base):
    """One mall customer from Shopping_data.csv.

    Column mapping from the CSV:
      CustomerID              -> id
      Genre                   -> genre
      Age                     -> age
      Annual Income (k$)      -> annual_income_k
      Spending Score (1-100)  -> spending_score
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    genre: Mapped[str] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    annual_income_k: Mapped[int] = mapped_column(nullable=False)
    spending_score: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        CheckConstraint("genre IN ('Male', 'Female')", name="ck_customers_genre"),
        CheckConstraint("age > 0", name="ck_customers_age"),
        CheckConstraint("annual_income_k >= 0", name="ck_customers_income"),
        CheckConstraint(
            "spending_score BETWEEN 1 AND 100", name="ck_customers_score"
        ),
        Index("ix_customers_genre", "genre"),
        Index("ix_customers_annual_income_k", "annual_income_k"),
        Index("ix_customers_spending_score", "spending_score"),
    )
