from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    age: int
    gender: str
    item_purchased: str
    category: str
    purchase_amount_usd: float
    location: str
    size: str
    color: str
    season: str
    review_rating: float
    subscription_status: str
    payment_method: str
    shipping_type: str
    discount_applied: str
    promo_code_used: str
    previous_purchases: int
    frequency_of_purchases: str


class PageMeta(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    pages: int = Field(..., ge=0)


class PurchasePage(BaseModel):
    meta: PageMeta
    items: list[PurchaseOut]


class CategoryStat(BaseModel):
    category: str
    count: int
    total_amount: float
    avg_amount: float
    avg_rating: float


class StatsOut(BaseModel):
    total_purchases: int
    total_revenue_usd: float
    avg_purchase_amount_usd: float
    avg_review_rating: float
    by_category: list[CategoryStat]
