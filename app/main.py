"""FastAPI application factory and HTTP routes."""

from __future__ import annotations

import math
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as PathParameter, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import csv_path as configured_csv_path
from .config import database_path as configured_database_path
from .database import customer_count, initialize_database
from .import_data import ImportValidationError, import_customers
from .models import Customer, CustomerPage, ErrorResponse, HealthResponse
from .repository import CustomerFilters, get_customer, list_customers


def _bad_range(minimum: int | None, maximum: int | None, name: str) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(status_code=400, detail=f"{name} minimum cannot exceed maximum")


def create_app(
    *, database_path: Path | None = None, seed_csv_path: Path | None = None
) -> FastAPI:
    database = database_path or configured_database_path()
    source_csv = seed_csv_path or configured_csv_path()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(database)
        if customer_count(database) == 0:
            try:
                import_customers(source_csv, database)
            except ImportValidationError as error:
                raise RuntimeError(f"Unable to seed customer database: {error}") from error
        yield

    api = FastAPI(
        title="Shopping Customer API",
        version="1.0.0",
        summary="Browse and filter the shopping customer dataset.",
        lifespan=lifespan,
    )

    @api.exception_handler(RequestValidationError)
    async def validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        first_error = error.errors()[0]
        location = ".".join(str(part) for part in first_error["loc"] if part != "query")
        detail = f"Invalid {location}: {first_error['msg']}"
        return JSONResponse(status_code=422, content={"detail": detail})

    @api.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", customer_count=customer_count(database))

    @api.get(
        "/api/v1/customers",
        response_model=CustomerPage,
        responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
        tags=["customers"],
    )
    async def customers(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        genre: str | None = Query(None, pattern="^(?i:male|female)$"),
        min_age: int | None = Query(None, ge=0, le=120),
        max_age: int | None = Query(None, ge=0, le=120),
        min_income: int | None = Query(None, ge=0),
        max_income: int | None = Query(None, ge=0),
        min_spending_score: int | None = Query(None, ge=1, le=100),
        max_spending_score: int | None = Query(None, ge=1, le=100),
        q: str | None = Query(None, min_length=1, max_length=50),
    ) -> CustomerPage:
        _bad_range(min_age, max_age, "age")
        _bad_range(min_income, max_income, "income")
        _bad_range(min_spending_score, max_spending_score, "spending score")
        filters = CustomerFilters(
            genre=genre.title() if genre else None,
            min_age=min_age,
            max_age=max_age,
            min_income=min_income,
            max_income=max_income,
            min_spending_score=min_spending_score,
            max_spending_score=max_spending_score,
            query=q,
        )
        rows, total = list_customers(database, filters, page, page_size)
        return CustomerPage(
            items=[Customer(**dict(row)) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size),
        )

    @api.get(
        "/api/v1/customers/{customer_id}",
        response_model=Customer,
        responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
        tags=["customers"],
    )
    async def customer(
        customer_id: str = PathParameter(..., min_length=1, max_length=32),
    ) -> Customer:
        row = get_customer(database, customer_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id!r} not found")
        return Customer(**dict(row))

    return api


app = create_app()
