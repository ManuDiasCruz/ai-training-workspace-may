from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: str = Field(examples=["0001"])
    genre: Literal["Male", "Female"]
    age: int = Field(ge=0, le=120, examples=[19])
    annual_income_k: int = Field(ge=0, examples=[15])
    spending_score: int = Field(ge=1, le=100, examples=[39])


class Pagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class CustomerListResponse(BaseModel):
    data: list[Customer]
    pagination: Pagination


class DatasetStats(BaseModel):
    total_records: int
    genres: dict[str, int]
    age_min: int
    age_max: int
    annual_income_k_min: int
    annual_income_k_max: int
    spending_score_min: int
    spending_score_max: int

