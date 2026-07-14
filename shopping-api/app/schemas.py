"""Pydantic schemas for request validation and response serialization."""
from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field


class Gender(str, enum.Enum):
    """Allowed values for the ``gender`` field (from the CSV ``Genre`` column)."""

    male = "Male"
    female = "Female"


class SortField(str, enum.Enum):
    """Columns that records may be sorted by."""

    customer_id = "customer_id"
    age = "age"
    annual_income_k = "annual_income_k"
    spending_score = "spending_score"


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"


class CustomerOut(BaseModel):
    """A single customer record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(..., examples=["0001"])
    gender: str = Field(..., examples=["Male"])
    age: int = Field(..., examples=[19])
    annual_income_k: int = Field(..., description="Annual income in thousands of USD (k$)", examples=[15])
    spending_score: int = Field(..., description="Spending score, 1-100", examples=[39])


class PageMeta(BaseModel):
    """Pagination metadata attached to list responses."""

    page: int = Field(..., ge=1, examples=[1])
    page_size: int = Field(..., ge=1, examples=[20])
    total: int = Field(..., ge=0, description="Total records matching the filters", examples=[200])
    total_pages: int = Field(..., ge=0, examples=[10])


class PaginatedCustomers(BaseModel):
    """Envelope returned by ``GET /customers``."""

    meta: PageMeta
    items: list[CustomerOut]


class GenderStats(BaseModel):
    gender: str
    count: int


class Stats(BaseModel):
    """Aggregate summary returned by ``GET /stats``."""

    total_customers: int
    by_gender: list[GenderStats]
    age: "MetricSummary"
    annual_income_k: "MetricSummary"
    spending_score: "MetricSummary"


class MetricSummary(BaseModel):
    min: float | None
    max: float | None
    avg: float | None


class ErrorResponse(BaseModel):
    """Uniform error body used by custom error handlers."""

    detail: str


# Resolve forward references for the nested ``MetricSummary``.
Stats.model_rebuild()
