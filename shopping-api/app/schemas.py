"""Pydantic response models for the Shopping Customers API."""

from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: int = Field(..., examples=[1])
    genre: str = Field(..., examples=["Male"])
    age: int = Field(..., examples=[19])
    annual_income_k: int = Field(..., description="Annual income in thousands of dollars", examples=[15])
    spending_score: int = Field(..., description="Store-assigned score from 1 to 100", examples=[39])


class CustomerPage(BaseModel):
    items: list[Customer]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class GenreBreakdown(BaseModel):
    genre: str
    customers: int
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
    by_genre: list[GenreBreakdown]
