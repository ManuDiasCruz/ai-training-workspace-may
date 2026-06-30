"""API response models."""

from typing import Literal

from pydantic import BaseModel, Field


Gender = Literal["Female", "Male"]


class Customer(BaseModel):
    customer_id: str = Field(pattern=r"^\d{4}$", examples=["0001"])
    gender: Gender
    age: int = Field(ge=0, le=120)
    annual_income_k: int = Field(ge=0, description="Annual income in thousands of USD")
    spending_score: int = Field(ge=1, le=100)


class Pagination(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class CustomerPage(BaseModel):
    items: list[Customer]
    pagination: Pagination


class HealthStatus(BaseModel):
    status: Literal["ok"]
    database: Literal["ready"]
    customer_count: int = Field(ge=0)

