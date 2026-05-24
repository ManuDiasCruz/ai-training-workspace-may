from __future__ import annotations

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    genre: Mapped[str] = mapped_column(String(16), index=True)
    age: Mapped[int] = mapped_column(Integer)
    annual_income_k: Mapped[int] = mapped_column(Integer)
    spending_score: Mapped[int] = mapped_column(Integer)


Index("ix_customers_genre_age", Customer.genre, Customer.age)
Index("ix_customers_income_score", Customer.annual_income_k, Customer.spending_score)
