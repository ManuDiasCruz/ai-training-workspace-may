"""Pydantic schemas for the customers REST API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Genre = Literal["Male", "Female"]


class CustomerBase(BaseModel):
    genre: Genre = Field(..., description="Customer genre, 'Male' or 'Female'.")
    age: int = Field(..., ge=0, le=150)
    annual_income_k: int = Field(..., ge=0, description="Annual income in thousands of dollars.")
    spending_score: int = Field(..., ge=1, le=100)


class CustomerCreate(CustomerBase):
    customer_id: int | None = Field(
        default=None,
        ge=1,
        description="Optional explicit ID. Auto-assigned when omitted.",
    )


class CustomerUpdate(BaseModel):
    genre: Genre | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    annual_income_k: int | None = Field(default=None, ge=0)
    spending_score: int | None = Field(default=None, ge=1, le=100)


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class CustomerPage(BaseModel):
    meta: PageMeta
    items: list[CustomerOut]


class Stats(BaseModel):
    total: int
    by_genre: dict[str, int]
    age: dict[str, float]
    annual_income_k: dict[str, float]
    spending_score: dict[str, float]
