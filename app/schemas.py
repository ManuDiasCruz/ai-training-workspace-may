from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerOut(BaseModel):
    customer_id: str
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


class PaginationMeta(BaseModel):
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)


class CustomerListResponse(BaseModel):
    meta: PaginationMeta
    items: list[CustomerOut]


class GenreBreakdown(BaseModel):
    genre: str
    count: int
    average_age: float
    average_annual_income_k: float
    average_spending_score: float


class SummaryResponse(BaseModel):
    total_customers: int
    average_age: float
    average_annual_income_k: float
    average_spending_score: float
    by_genre: list[GenreBreakdown]
