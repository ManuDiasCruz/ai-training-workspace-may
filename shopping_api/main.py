from __future__ import annotations

import math
import sqlite3
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from shopping_api.database import database_connection, initialize_database
from shopping_api.repository import CustomerFilters, get_customer, list_customers
from shopping_api.schemas import Customer, CustomerPage, HealthResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Shopping Customer API",
    version="1.0.0",
    description="Read-only API for browsing and filtering shopping customer data.",
    lifespan=lifespan,
)


@app.exception_handler(sqlite3.Error)
async def database_error_handler(_: Request, __: sqlite3.Error) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred."},
    )


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health(connection: sqlite3.Connection = Depends(database_connection)) -> HealthResponse:
    records = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return HealthResponse(status="ok", records=records)


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
async def customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    gender: Literal["Male", "Female"] | None = None,
    min_age: int | None = Query(None, ge=0, le=120),
    max_age: int | None = Query(None, ge=0, le=120),
    min_income: int | None = Query(None, ge=0),
    max_income: int | None = Query(None, ge=0),
    min_spending_score: int | None = Query(None, ge=1, le=100),
    max_spending_score: int | None = Query(None, ge=1, le=100),
    q: str | None = Query(None, min_length=1, max_length=50),
    connection: sqlite3.Connection = Depends(database_connection),
) -> CustomerPage:
    ranges = [
        ("age", min_age, max_age),
        ("income", min_income, max_income),
        ("spending score", min_spending_score, max_spending_score),
    ]
    for field, minimum, maximum in ranges:
        if minimum is not None and maximum is not None and minimum > maximum:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum {field} cannot be greater than maximum {field}.",
            )

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
    items, total = list_customers(connection, filters, page, page_size)
    return CustomerPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size),
    )


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
async def customer_detail(
    customer_id: str,
    connection: sqlite3.Connection = Depends(database_connection),
) -> Customer:
    if len(customer_id) != 4 or not customer_id.isdigit():
        raise HTTPException(status_code=422, detail="customer_id must contain exactly four digits.")

    customer = get_customer(connection, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return Customer(**customer)
