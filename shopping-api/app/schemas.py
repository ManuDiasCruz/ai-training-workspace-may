"""Pydantic schemas describing API request/response payloads."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Gender(str, Enum):
    """Allowed values for the customer gender field."""

    male = "Male"
    female = "Female"


class SortField(str, Enum):
    """Fields that the customer list can be sorted by."""

    customer_id = "customer_id"
    age = "age"
    annual_income = "annual_income"
    spending_score = "spending_score"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class CustomerOut(BaseModel):
    """A customer record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(..., examples=["0001"], description="Business identifier from the dataset")
    gender: str = Field(..., examples=["Male"])
    age: int = Field(..., examples=[19])
    annual_income: int = Field(..., examples=[15], description="Annual income in thousands of dollars (k$)")
    spending_score: int = Field(..., examples=[39], description="Mall spending score, 1-100")


class PageMeta(BaseModel):
    """Pagination metadata attached to list responses."""

    total: int = Field(..., description="Total records matching the query (ignoring pagination)")
    limit: int = Field(..., description="Maximum records requested per page")
    offset: int = Field(..., description="Number of records skipped")
    count: int = Field(..., description="Records actually returned on this page")


class PaginatedCustomers(BaseModel):
    """A page of customer records."""

    meta: PageMeta
    items: list[CustomerOut]


class FieldStats(BaseModel):
    """Descriptive statistics for a single numeric field."""

    min: float
    max: float
    avg: float


class StatsOut(BaseModel):
    """Aggregate statistics across the whole dataset."""

    total_customers: int
    gender_breakdown: dict[str, int]
    age: FieldStats
    annual_income: FieldStats
    spending_score: FieldStats


class ErrorResponse(BaseModel):
    """Uniform error envelope used by the API's exception handlers."""

    detail: str
