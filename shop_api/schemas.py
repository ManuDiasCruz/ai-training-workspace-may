"""Public request and response models for the shopping API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Gender(str, Enum):
    female = "female"
    male = "male"


class Customer(BaseModel):
    customer_id: str = Field(description="Original zero-padded, four-digit customer ID.")
    gender: str
    age: int
    annual_income_k_usd: int = Field(
        description="Annual income expressed in thousands of US dollars."
    )
    spending_score: int = Field(description="Original dataset score from 0 to 100.")


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class CustomerPage(BaseModel):
    items: list[Customer]
    pagination: Pagination


class NumericSummary(BaseModel):
    minimum: int
    maximum: int
    average: float


class DatasetStatistics(BaseModel):
    total_customers: int
    gender_breakdown: dict[str, int]
    age: NumericSummary
    annual_income_k_usd: NumericSummary
    spending_score: NumericSummary


class HealthStatus(BaseModel):
    status: str
    database: str
    customer_count: int

