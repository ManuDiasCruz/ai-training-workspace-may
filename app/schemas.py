"""Pydantic response models for the public API contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Gender = Literal["Male", "Female"]


class Customer(BaseModel):
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


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["reachable"]
