"""Pydantic schemas for request validation and response serialization."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    genre: str = Field(..., pattern="^(Male|Female)$", description="Male or Female")
    age: int = Field(..., ge=0, le=120)
    annual_income: int = Field(..., ge=0, description="Annual income in thousands of dollars (k$)")
    spending_score: int = Field(..., ge=1, le=100, description="Spending score from 1 to 100")


class CustomerCreate(CustomerBase):
    customer_id: str = Field(..., min_length=1, max_length=16)


class Customer(CustomerBase):
    """Customer as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str


class PaginatedCustomers(BaseModel):
    """A page of customer records plus pagination metadata."""

    total: int = Field(..., description="Total records matching the query (ignoring pagination)")
    limit: int
    offset: int
    count: int = Field(..., description="Number of records in this page")
    items: List[Customer]


class StatsSummary(BaseModel):
    """Aggregate statistics over the (optionally filtered) dataset."""

    total: int
    avg_age: Optional[float] = None
    avg_annual_income: Optional[float] = None
    avg_spending_score: Optional[float] = None
    genre_breakdown: dict


class ErrorResponse(BaseModel):
    detail: str
