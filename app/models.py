from typing import Literal

from pydantic import BaseModel, Field


class CustomerResponse(BaseModel):
    customer_id: str = Field(examples=["0001"])
    genre: Literal["Male", "Female"]
    age: int
    annual_income_k: int = Field(
        description="Annual income in thousands of US dollars."
    )
    spending_score: int = Field(
        description="Dataset spending score on a 1-100 scale."
    )


class CustomerPage(BaseModel):
    items: list[CustomerResponse]
    page: int
    page_size: int
    total: int
    pages: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ready"]
    customer_count: int

