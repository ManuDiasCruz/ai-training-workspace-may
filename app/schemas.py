"""Pydantic request/response models (API contract & validation)."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Gender(str, Enum):
    """Allowed gender values (matches the values stored in the database)."""

    male = "Male"
    female = "Female"


class SortField(str, Enum):
    """Columns the customer list may be sorted by."""

    customer_id = "customer_id"
    age = "age"
    annual_income_k = "annual_income_k"
    spending_score = "spending_score"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class CustomerOut(BaseModel):
    """A customer record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: int = Field(..., examples=[1], description="Unique customer identifier.")
    gender: str = Field(..., examples=["Male"], description="Customer gender.")
    age: int = Field(..., examples=[19], description="Customer age in years.")
    annual_income_k: int = Field(
        ..., examples=[15], description="Annual income in thousands of dollars (k$)."
    )
    spending_score: int = Field(
        ..., examples=[39], description="Spending score assigned by the mall (1-100)."
    )


class PaginationMeta(BaseModel):
    """Pagination metadata accompanying a list response."""

    page: int = Field(..., description="Current 1-based page number.")
    page_size: int = Field(..., description="Number of items requested per page.")
    total_items: int = Field(..., description="Total records matching the query.")
    total_pages: int = Field(..., description="Total number of pages available.")
    has_next: bool
    has_previous: bool


class CustomerListResponse(BaseModel):
    data: list[CustomerOut]
    pagination: PaginationMeta


class NumericStat(BaseModel):
    min: int | None = None
    max: int | None = None
    average: float | None = None


class StatsResponse(BaseModel):
    """Aggregate statistics for the (optionally filtered) customer set."""

    total_customers: int
    gender_distribution: dict[str, int]
    age: NumericStat
    annual_income_k: NumericStat
    spending_score: NumericStat
    filters_applied: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    customers_loaded: int = Field(..., examples=[200])


class ErrorDetail(BaseModel):
    status: int
    message: str
    details: list[Any] | None = None


class ErrorResponse(BaseModel):
    """Consistent error envelope returned for 4xx/5xx responses."""

    error: ErrorDetail
