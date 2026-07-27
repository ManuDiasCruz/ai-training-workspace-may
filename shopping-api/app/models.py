"""Response models for the read-only customer API."""

from pydantic import BaseModel, ConfigDict, Field


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(description="Four-digit source identifier, including leading zeroes")
    gender: str = Field(description="Value from the source CSV's Genre column")
    age: int
    annual_income_k: int = Field(description="Annual income in thousands of US dollars")
    spending_score: int = Field(description="Source spending score from 1 to 100")


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    page: int
    page_size: int
    total_pages: int
    next_page: int | None
    previous_page: int | None


class HealthResponse(BaseModel):
    status: str
    records: int
