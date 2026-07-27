"""FastAPI application for shopping-customer exploration."""

from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from app.config import database_path
from app.database import get_connection, initialize_database
from app.repository import CustomerFilters, get_customer, list_customers
from app.schemas import Customer, CustomerPage, HealthResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Shopping Customer API",
    version="1.0.0",
    description="Read-only REST API backed by the shopping customer dataset and SQLite.",
    lifespan=lifespan,
)


@app.exception_handler(sqlite3.DatabaseError)
async def database_error_handler(_: Request, exc: sqlite3.DatabaseError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is temporarily unavailable", "error": type(exc).__name__},
    )


def _validate_range(name: str, minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(status_code=422, detail=f"{name} minimum cannot exceed maximum")


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health(connection: Annotated[sqlite3.Connection, Depends(get_connection)]) -> HealthResponse:
    count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return HealthResponse(status="ok", database=database_path().name, customer_count=count)


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
def customers(
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    page: Annotated[int, Query(ge=1, description="One-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    gender: Literal["Male", "Female"] | None = None,
    min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0)] = None,
    max_income: Annotated[int | None, Query(ge=0)] = None,
    min_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=50, description="Simple text search")] = None,
) -> CustomerPage:
    _validate_range("age", min_age, max_age)
    _validate_range("income", min_income, max_income)
    _validate_range("spending score", min_spending_score, max_spending_score)
    filters = CustomerFilters(
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_spending_score=min_spending_score,
        max_spending_score=max_spending_score,
        query=q.strip() if q else None,
    )
    return CustomerPage(**list_customers(connection, filters, page, page_size))


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
def customer_by_id(
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    customer_id: Annotated[str, Path(min_length=1, max_length=20, pattern=r"^\d+$")],
) -> Customer:
    customer = get_customer(connection, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**customer)
