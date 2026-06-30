"""Pydantic schemas for request/response validation and serialization."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class CustomerOut(BaseModel):
    """Serialized customer record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: int = Field(..., description="Unique customer identifier", examples=[1])
    genre: str = Field(..., description="Customer gender", examples=["Female"])
    age: int = Field(..., description="Customer age in years", examples=[31])
    annual_income_k: int = Field(
        ..., description="Annual income in thousands of dollars (k$)", examples=[40]
    )
    spending_score: int = Field(
        ..., description="Spending score assigned by the mall (1-100)", examples=[42]
    )


class PaginatedCustomers(BaseModel):
    """A page of customer records plus pagination metadata."""

    total: int = Field(..., description="Total records matching the query")
    limit: int = Field(..., description="Page size used for this response")
    offset: int = Field(..., description="Number of records skipped")
    count: int = Field(..., description="Number of records in this page")
    items: List[CustomerOut] = Field(..., description="The records on this page")


class StatsOut(BaseModel):
    """Aggregate statistics across the (optionally filtered) dataset."""

    total_customers: int
    male_count: int
    female_count: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float
    min_annual_income_k: int
    max_annual_income_k: int
