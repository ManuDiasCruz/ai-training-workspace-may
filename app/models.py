"""Public API response models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Gender(str, Enum):
    male = "Male"
    female = "Female"


class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(pattern=r"^\d{4}$", examples=["0001"])
    gender: Gender
    age: int = Field(ge=0, le=120)
    annual_income_kusd: int = Field(ge=0)
    spending_score: int = Field(ge=1, le=100)


class CustomerPage(BaseModel):
    items: list[Customer]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class HealthStatus(BaseModel):
    status: str
    records: int = Field(ge=0)

