"""SQLAlchemy ORM models for the shopping dataset."""

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Customer(Base):
    """A single mall customer record from the shopping dataset.

    Columns map directly to the CSV fields:
      CustomerID, Genre, Age, Annual Income (k$), Spending Score (1-100)
    """

    __tablename__ = "customers"

    # CustomerID is the natural primary key from the dataset (e.g. 1..200).
    customer_id: Mapped[int] = mapped_column("customer_id", Integer, primary_key=True)
    genre: Mapped[str] = mapped_column(String, nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    annual_income_k: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    spending_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("genre IN ('Male', 'Female')", name="ck_genre_valid"),
        CheckConstraint("age >= 0", name="ck_age_non_negative"),
        CheckConstraint("annual_income_k >= 0", name="ck_income_non_negative"),
        CheckConstraint(
            "spending_score >= 1 AND spending_score <= 100",
            name="ck_spending_score_range",
        ),
    )
