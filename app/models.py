"""API request and response models."""

from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: str = Field(description="Original zero-padded customer identifier")
    genre: str
    age: int
    annual_income_k: int = Field(description="Annual income in thousands of dollars")
    spending_score: int = Field(description="Dataset spending score from 1 to 100")


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    page: int
    page_size: int
    pages: int


class HealthResponse(BaseModel):
    status: str
    customer_count: int


class ErrorResponse(BaseModel):
    detail: str
