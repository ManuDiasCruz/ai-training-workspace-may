"""FastAPI application for exploring the shopping customer dataset."""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from math import ceil
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as ApiPath, Query, Request
from fastapi.responses import JSONResponse

from app.database import DEFAULT_DATABASE_PATH, initialize_database
from app.models import Customer, CustomerPage, Gender, HealthStatus
from app.repository import count_customers, get_customer, list_customers


LOGGER = logging.getLogger(__name__)


def _validate_bounds(
    minimum: int | None,
    maximum: int | None,
    field_name: str,
) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=422,
            detail=f"min_{field_name} cannot be greater than max_{field_name}",
        )


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Build an application, optionally bound to a custom SQLite database."""

    configured_path = Path(
        database_path
        or os.getenv("SHOPPING_DATABASE_PATH", str(DEFAULT_DATABASE_PATH))
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialize_database(application.state.database_path)
        yield

    application = FastAPI(
        title="Shopping Dataset API",
        summary="Browse and filter customer shopping records persisted in SQLite.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.database_path = configured_path

    @application.exception_handler(sqlite3.Error)
    async def handle_database_error(
        request: Request, exc: sqlite3.Error
    ) -> JSONResponse:
        LOGGER.exception("Database error while serving %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "The database could not complete the request."},
        )

    @application.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {
            "name": "Shopping Dataset API",
            "documentation": "/docs",
            "health": "/health",
        }

    @application.get("/health", response_model=HealthStatus, tags=["meta"])
    def health() -> HealthStatus:
        return HealthStatus(
            status="ok",
            database="ready",
            customer_count=count_customers(application.state.database_path),
        )

    @application.get("/customers", response_model=CustomerPage, tags=["customers"])
    def customers(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        gender: Gender | None = Query(None),
        min_age: int | None = Query(None, ge=0, le=120),
        max_age: int | None = Query(None, ge=0, le=120),
        min_income: int | None = Query(None, ge=0),
        max_income: int | None = Query(None, ge=0),
        min_spending_score: int | None = Query(None, ge=1, le=100),
        max_spending_score: int | None = Query(None, ge=1, le=100),
        search: str | None = Query(None, min_length=1, max_length=50),
    ) -> CustomerPage:
        _validate_bounds(min_age, max_age, "age")
        _validate_bounds(min_income, max_income, "income")
        _validate_bounds(
            min_spending_score, max_spending_score, "spending_score"
        )

        normalized_search = search.strip() if search else None
        if search is not None and not normalized_search:
            raise HTTPException(
                status_code=422, detail="search must include a non-whitespace character"
            )

        items, total = list_customers(
            application.state.database_path,
            page=page,
            page_size=page_size,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
            min_income=min_income,
            max_income=max_income,
            min_spending_score=min_spending_score,
            max_spending_score=max_spending_score,
            search=normalized_search,
        )
        return CustomerPage(
            items=items,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": ceil(total / page_size) if total else 0,
            },
        )

    @application.get(
        "/customers/{customer_id}", response_model=Customer, tags=["customers"]
    )
    def customer(
        customer_id: str = ApiPath(pattern=r"^\d{4}$", examples=["0001"]),
    ) -> Customer:
        record = get_customer(application.state.database_path, customer_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer(**record)

    return application


app = create_app()

