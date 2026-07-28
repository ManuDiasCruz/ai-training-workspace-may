"""Pydantic models: request validation and response shapes."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.functional_validators import BeforeValidator

from . import config

Gender = Literal["Male", "Female"]
Segment = Literal["careless", "frugal", "target", "cautious", "standard"]

SortField = Literal["customer_id", "age", "annual_income_k", "spending_score"]
SortOrder = Literal["asc", "desc"]


def _normalize_gender(value: object) -> object:
    """Accept 'male'/'MALE'/'male ' as 'Male' so the filter is forgiving."""
    if isinstance(value, str):
        return value.strip().capitalize()
    return value


def _normalize_lower(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value


class Customer(BaseModel):
    """A single dataset record, as returned by the API."""

    customer_id: str = Field(examples=["0001"], description="Canonical zero-padded id")
    gender: Gender
    age: int = Field(examples=[19])
    annual_income_k: int = Field(
        examples=[15], description="Annual income in thousands of USD (k$)"
    )
    spending_score: int = Field(examples=[39], description="Spending score, 1-100")
    segment: Segment = Field(description="Heuristic income/spending quadrant")


class PageMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CustomerPage(BaseModel):
    meta: PageMeta
    data: list[Customer]


class CustomerListQuery(BaseModel):
    """Query parameters for `GET /customers`.

    `extra="forbid"` makes a misspelled parameter a 422 instead of a silently
    ignored filter, which is the more useful failure for an API client.
    """

    model_config = ConfigDict(extra="forbid")

    page: int = Field(1, ge=1, description="1-based page number")
    page_size: int = Field(
        config.DEFAULT_PAGE_SIZE,
        ge=1,
        le=config.MAX_PAGE_SIZE,
        description=f"Records per page (max {config.MAX_PAGE_SIZE})",
    )

    gender: Annotated[Gender, BeforeValidator(_normalize_gender)] | None = None
    segment: Annotated[Segment, BeforeValidator(_normalize_lower)] | None = None

    age_min: int | None = Field(None, ge=0, le=120)
    age_max: int | None = Field(None, ge=0, le=120)
    income_min: int | None = Field(None, ge=0, description="Minimum income in k$")
    income_max: int | None = Field(None, ge=0, description="Maximum income in k$")
    score_min: int | None = Field(None, ge=1, le=100)
    score_max: int | None = Field(None, ge=1, le=100)

    q: str | None = Field(
        None,
        max_length=64,
        description="Free-text search across customer_id and gender",
    )

    sort_by: SortField = "customer_id"
    order: SortOrder = "asc"

    @model_validator(mode="after")
    def _check_ranges(self) -> CustomerListQuery:
        """Reject inverted ranges, which would otherwise return an empty page."""
        pairs = (
            ("age_min", "age_max"),
            ("income_min", "income_max"),
            ("score_min", "score_max"),
        )
        for low_name, high_name in pairs:
            low, high = getattr(self, low_name), getattr(self, high_name)
            if low is not None and high is not None and low > high:
                raise ValueError(
                    f"{low_name} ({low}) must be less than or equal to "
                    f"{high_name} ({high})"
                )
        return self


class GenderBreakdown(BaseModel):
    gender: Gender
    count: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class SegmentBreakdown(BaseModel):
    segment: Segment
    count: int
    avg_annual_income_k: float
    avg_spending_score: float


class NumericSummary(BaseModel):
    min: int
    max: int
    avg: float


class StatsResponse(BaseModel):
    total_customers: int
    age: NumericSummary
    annual_income_k: NumericSummary
    spending_score: NumericSummary
    by_gender: list[GenderBreakdown]
    by_segment: list[SegmentBreakdown]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: str
    record_count: int
    source_file: str | None = None
    imported_at: str | None = None


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    """Every error the API returns uses this envelope."""

    error: ErrorBody
