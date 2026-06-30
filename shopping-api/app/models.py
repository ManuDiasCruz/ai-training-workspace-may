"""SQLAlchemy ORM models for the shopping dataset."""
from sqlalchemy import CheckConstraint, Column, Integer, String

from .database import Base


class Customer(Base):
    """A single mall customer record from the shopping dataset.

    Columns map directly to the source CSV:
        CustomerID, Genre, Age, Annual Income (k$), Spending Score (1-100)
    """

    __tablename__ = "customers"

    # CustomerID is kept as a zero-padded string ("0001") to preserve the
    # original identifiers exactly as they appear in the dataset.
    customer_id = Column(String, primary_key=True, index=True)
    genre = Column(String, nullable=False, index=True)
    age = Column(Integer, nullable=False, index=True)
    annual_income = Column(Integer, nullable=False, index=True)
    spending_score = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("genre IN ('Male', 'Female')", name="ck_genre"),
        CheckConstraint("age >= 0", name="ck_age"),
        CheckConstraint("annual_income >= 0", name="ck_income"),
        CheckConstraint(
            "spending_score >= 1 AND spending_score <= 100",
            name="ck_spending_score",
        ),
    )
