"""API response contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: str
    gender: str
    age: int
    annual_income_k: int = Field(description="Annual income in thousands of dollars")
    spending_score: int = Field(ge=1, le=100)


class CustomerPage(BaseModel):
    items: list[Customer]
    page: int
    page_size: int
    total: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str
    database: str
    customer_count: int
