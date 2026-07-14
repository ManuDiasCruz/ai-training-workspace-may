"""Pydantic response schemas."""

from pydantic import BaseModel, ConfigDict


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


class PaginatedCustomers(BaseModel):
    items: list[CustomerOut]
    total: int
    page: int
    page_size: int
    pages: int


class GenreStats(BaseModel):
    count: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class StatsOut(BaseModel):
    total_customers: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float
    by_genre: dict[str, GenreStats]
