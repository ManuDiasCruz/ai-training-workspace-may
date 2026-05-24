from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: str
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


class PageMeta(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    pages: int = Field(..., ge=0)


class CustomerPage(BaseModel):
    meta: PageMeta
    items: list[CustomerOut]


class GenreStat(BaseModel):
    genre: str
    count: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class StatsOut(BaseModel):
    total_customers: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float
    min_age: int | None = None
    max_age: int | None = None
    min_annual_income_k: int | None = None
    max_annual_income_k: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    by_genre: list[GenreStat]
