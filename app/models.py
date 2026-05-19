from __future__ import annotations

from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(16), index=True)
    item_purchased: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    purchase_amount_usd: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String(64), index=True)
    size: Mapped[str] = mapped_column(String(8))
    color: Mapped[str] = mapped_column(String(32))
    season: Mapped[str] = mapped_column(String(16), index=True)
    review_rating: Mapped[float] = mapped_column(Float)
    subscription_status: Mapped[str] = mapped_column(String(8))
    payment_method: Mapped[str] = mapped_column(String(32))
    shipping_type: Mapped[str] = mapped_column(String(32))
    discount_applied: Mapped[str] = mapped_column(String(8))
    promo_code_used: Mapped[str] = mapped_column(String(8))
    previous_purchases: Mapped[int] = mapped_column(Integer)
    frequency_of_purchases: Mapped[str] = mapped_column(String(32))


Index("ix_purchases_category_location", Purchase.category, Purchase.location)
