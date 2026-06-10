"""Pydantic models describing the API's request and response payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: int = Field(examples=[1])
    genre: str = Field(examples=["Male"], description="Gender as labelled in the source dataset")
    age: int = Field(examples=[19])
    annual_income_k: int = Field(examples=[15], description="Annual income in thousands of dollars")
    spending_score: int = Field(examples=[39], description="Store-assigned spending score from 1 to 100")


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CustomerListResponse(BaseModel):
    items: list[Customer]
    pagination: Pagination


class FieldSummary(BaseModel):
    min: int | None
    max: int | None
    avg: float | None


class StatsResponse(BaseModel):
    total_customers: int
    genre_counts: dict[str, int]
    age: FieldSummary
    annual_income_k: FieldSummary
    spending_score: FieldSummary


class ErrorBody(BaseModel):
    code: int
    message: str
    details: list | None = None


class ErrorResponse(BaseModel):
    """Envelope used by every non-2xx response."""

    error: ErrorBody
