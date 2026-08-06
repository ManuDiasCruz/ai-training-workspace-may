"""Pydantic response models for the shopping API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Genre(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class SortField(str, Enum):
    ID = "id"
    AGE = "age"
    ANNUAL_INCOME_K = "annual_income_k"
    SPENDING_SCORE = "spending_score"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class Customer(BaseModel):
    id: int = Field(examples=[1])
    genre: Genre
    age: int = Field(ge=1, le=120, examples=[19])
    annual_income_k: int = Field(ge=0, examples=[15])
    spending_score: int = Field(ge=1, le=100, examples=[39])


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    page: int
    page_size: int
    pages: int


class GenreStats(BaseModel):
    count: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class Stats(BaseModel):
    total_customers: int
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float
    by_genre: dict[str, GenreStats]
