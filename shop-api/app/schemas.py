"""Pydantic response models for the shop API."""

from pydantic import BaseModel


class Customer(BaseModel):
    customer_id: int
    genre: str
    age: int
    annual_income: int
    spending_score: int


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    page: int
    page_size: int
    pages: int


class GenreStats(BaseModel):
    genre: str
    count: int
    avg_age: float
    avg_annual_income: float
    avg_spending_score: float


class Stats(BaseModel):
    total_customers: int
    avg_age: float
    avg_annual_income: float
    avg_spending_score: float
    by_genre: list[GenreStats]
