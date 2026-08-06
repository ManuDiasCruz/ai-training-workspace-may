"""Pydantic response models."""

from pydantic import BaseModel


class Customer(BaseModel):
    customer_id: int
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    page: int
    page_size: int
    pages: int


class GenreStats(BaseModel):
    count: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class StatsSummary(BaseModel):
    total_customers: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float
    min_annual_income_k: int
    max_annual_income_k: int
    by_genre: dict[str, GenreStats]
