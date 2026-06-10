from pydantic import BaseModel


class Customer(BaseModel):
    customer_id: str
    gender: str
    age: int
    annual_income_k: int
    spending_score: int


class CustomerPage(BaseModel):
    items: list[Customer]
    page: int
    page_size: int
    total: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str
    records: int

