"""API response models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(examples=["0001"])
    gender: Gender
    age: int = Field(ge=0, le=120)
    annual_income_kusd: int = Field(ge=0)
    spending_score: int = Field(ge=1, le=100)


class Pagination(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_previous: bool
    has_next: bool


class CustomerList(BaseModel):
    items: list[Customer]
    pagination: Pagination


class DatasetMetadata(BaseModel):
    source_file: str
    source_url: str
    source_modified_at: str | None
    imported_at: str
    record_count: int = Field(ge=0)


class Health(BaseModel):
    status: str
    database: str
    customer_count: int = Field(ge=0)
