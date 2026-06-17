from sqlalchemy import Column, Integer, String, CheckConstraint, Index

from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(8), unique=True, nullable=False, index=True)
    gender = Column(String(16), nullable=False)
    age = Column(Integer, nullable=False)
    annual_income_k = Column(Integer, nullable=False)
    spending_score = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "gender IN ('Male', 'Female')", name="ck_customer_gender_values"
        ),
        CheckConstraint("age >= 0 AND age <= 130", name="ck_customer_age_range"),
        CheckConstraint("annual_income_k >= 0", name="ck_customer_income_nonneg"),
        CheckConstraint(
            "spending_score >= 1 AND spending_score <= 100",
            name="ck_customer_spending_range",
        ),
        Index("ix_customers_gender_age", "gender", "age"),
    )
