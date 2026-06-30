"""FastAPI application exposing the persisted shopping dataset."""

from __future__ import annotations

import math
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from shopping_api.db import connect, initialize_database


class Customer(BaseModel):
    """One normalized row from the shopping dataset."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(examples=["0001"])
    genre: Literal["Female", "Male"]
    age: int
    annual_income_k: int = Field(description="Annual income in thousands of dollars")
    spending_score: int = Field(description="Dataset score from 1 to 100")


class CustomerPage(BaseModel):
    """A page of matching customers and its pagination metadata."""

    items: list[Customer]
    page: int
    page_size: int
    total: int
    pages: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    customer_count: int


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Shopping Dataset API",
    summary="Query a locally persisted customer shopping dataset.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(sqlite3.Error)
async def database_error_handler(_: Request, __: sqlite3.Error) -> JSONResponse:
    """Avoid exposing database implementation details to API callers."""

    return JSONResponse(status_code=500, content={"detail": "Database operation failed"})


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"name": "Shopping Dataset API", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    with connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return HealthResponse(status="ok", customer_count=count)


def _validate_range(name: str, minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=422,
            detail=f"{name}_min must be less than or equal to {name}_max",
        )


def _literal_like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
def list_customers(
    page: Annotated[int, Query(ge=1, description="One-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    genre: Annotated[Literal["Female", "Male"] | None, Query()] = None,
    age_min: Annotated[int | None, Query(ge=0, le=120)] = None,
    age_max: Annotated[int | None, Query(ge=0, le=120)] = None,
    income_min: Annotated[int | None, Query(ge=0)] = None,
    income_max: Annotated[int | None, Query(ge=0)] = None,
    score_min: Annotated[int | None, Query(ge=1, le=100)] = None,
    score_max: Annotated[int | None, Query(ge=1, le=100)] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=50, description="Substring search across all fields"),
    ] = None,
) -> CustomerPage:
    """List customers with pagination, range filters, genre filtering, and search."""

    _validate_range("age", age_min, age_max)
    _validate_range("income", income_min, income_max)
    _validate_range("score", score_min, score_max)

    clauses: list[str] = []
    parameters: list[object] = []

    if genre is not None:
        clauses.append("genre = ?")
        parameters.append(genre)

    range_filters = (
        ("age", age_min, age_max),
        ("annual_income_k", income_min, income_max),
        ("spending_score", score_min, score_max),
    )
    for column, minimum, maximum in range_filters:
        if minimum is not None:
            clauses.append(f"{column} >= ?")
            parameters.append(minimum)
        if maximum is not None:
            clauses.append(f"{column} <= ?")
            parameters.append(maximum)

    normalized_q = q.strip() if q else ""
    if normalized_q:
        pattern = _literal_like(normalized_q)
        searchable_columns = (
            "customer_id",
            "genre",
            "CAST(age AS TEXT)",
            "CAST(annual_income_k AS TEXT)",
            "CAST(spending_score AS TEXT)",
        )
        clauses.append(
            "(" + " OR ".join(f"{column} LIKE ? ESCAPE '\\' COLLATE NOCASE" for column in searchable_columns) + ")"
        )
        parameters.extend([pattern] * len(searchable_columns))

    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    offset = (page - 1) * page_size

    with connect() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM customers{where_clause}", parameters
        ).fetchone()[0]
        rows = connection.execute(
            f"""
            SELECT customer_id, genre, age, annual_income_k, spending_score
            FROM customers{where_clause}
            ORDER BY customer_id
            LIMIT ? OFFSET ?
            """,
            [*parameters, page_size, offset],
        ).fetchall()

    return CustomerPage(
        items=[Customer.model_validate(dict(row)) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size) if total else 0,
    )


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
def get_customer(
    customer_id: Annotated[str, Path(pattern=r"^\d{4}$", examples=["0001"])],
) -> Customer:
    """Return one customer by the zero-padded ID used in the source CSV."""

    with connect() as connection:
        row = connection.execute(
            """
            SELECT customer_id, genre, age, annual_income_k, spending_score
            FROM customers WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer.model_validate(dict(row))
