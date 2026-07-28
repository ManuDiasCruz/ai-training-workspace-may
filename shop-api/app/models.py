"""Pydantic models: the validation boundary for both the importer and the API."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Gender(str, Enum):
    female = "Female"
    male = "Male"


class Band(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AgeBracket(str, Enum):
    under_25 = "under-25"
    b25_34 = "25-34"
    b35_44 = "35-44"
    b45_54 = "45-54"
    b55_plus = "55-plus"


class SortField(str, Enum):
    id = "id"
    age = "age"
    annual_income_k = "annual_income_k"
    spending_score = "spending_score"
    gender = "gender"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class CustomerRow(BaseModel):
    """A single validated CSV row, on its way into the database.

    Enforces the same bounds as the CHECK constraints in schema.sql, so a bad
    row is reported with a readable message instead of a raw sqlite3 error.
    """

    id: int = Field(ge=1)
    customer_ref: str = Field(min_length=1, max_length=16)
    gender: Gender
    age: int = Field(ge=0, le=120)
    annual_income_k: int = Field(ge=0)
    spending_score: int = Field(ge=1, le=100)

    @field_validator("gender", mode="before")
    @classmethod
    def _normalise_gender(cls, value: Any) -> Any:
        """Accept 'male' / 'MALE ' from the CSV and canonicalise to 'Male'."""
        if isinstance(value, str):
            return value.strip().capitalize()
        return value


class Customer(BaseModel):
    """A customer as returned by the API, including DB-derived segment labels."""

    id: int
    customer_ref: str
    gender: Gender
    age: int
    annual_income_k: int
    spending_score: int
    age_bracket: AgeBracket
    income_band: Band
    spending_tier: Band


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CustomerPage(BaseModel):
    data: list[Customer]
    pagination: Pagination
    filters_applied: dict[str, Any]


class NumericSummary(BaseModel):
    min: int
    max: int
    avg: float


class GroupCount(BaseModel):
    value: str
    count: int
    avg_spending_score: float


class Stats(BaseModel):
    total_customers: int
    age: NumericSummary
    annual_income_k: NumericSummary
    spending_score: NumericSummary
    by_gender: list[GroupCount]
    by_income_band: list[GroupCount]
    by_spending_tier: list[GroupCount]
    by_age_bracket: list[GroupCount]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
