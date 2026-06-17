from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class Gender(str, Enum):
    male = "Male"
    female = "Female"


class CustomerBase(BaseModel):
    customer_code: str = Field(..., pattern=r"^\d{4,8}$")
    gender: Gender
    age: int = Field(..., ge=0, le=130)
    annual_income_k: int = Field(..., ge=0)
    spending_score: int = Field(..., ge=1, le=100)


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PaginatedCustomers(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CustomerOut]


class StatsOut(BaseModel):
    total_customers: int
    by_gender: dict
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class ErrorOut(BaseModel):
    detail: str
