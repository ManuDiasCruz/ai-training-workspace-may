from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    customer_code: str = Field(..., min_length=1, max_length=8)
    gender: str = Field(..., pattern="^(Male|Female)$")
    age: int = Field(..., ge=0, le=130)
    annual_income_k: int = Field(..., ge=0)
    spending_score: int = Field(..., ge=1, le=100)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    customer_code: Optional[str] = Field(None, min_length=1, max_length=8)
    gender: Optional[str] = Field(None, pattern="^(Male|Female)$")
    age: Optional[int] = Field(None, ge=0, le=130)
    annual_income_k: Optional[int] = Field(None, ge=0)
    spending_score: Optional[int] = Field(None, ge=1, le=100)


class CustomerOut(CustomerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PaginatedCustomers(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    items: List[CustomerOut]


class StatsOut(BaseModel):
    total_customers: int
    by_gender: dict
    avg_age: float
    avg_annual_income_k: float
    avg_spending_score: float


class ErrorOut(BaseModel):
    detail: str
