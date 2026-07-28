"""Pydantic response models for the shop API."""

from pydantic import BaseModel


class Customer(BaseModel):
    id: int
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


class CustomerPage(BaseModel):
    items: list[Customer]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class GenreStats(BaseModel):
    genre: str
    count: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class Stats(BaseModel):
    total_customers: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float
    min_annual_income_k: int
    max_annual_income_k: int
    by_genre: list[GenreStats]
