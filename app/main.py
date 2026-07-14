"""FastAPI application for browsing the shopping customer dataset."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Generator
from contextlib import asynccontextmanager
from math import ceil
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path as ApiPath, Query, Request
from fastapi.responses import JSONResponse

from app.database import (
    DEFAULT_DATABASE_PATH,
    DEFAULT_DATASET_PATH,
    connect,
    initialize_database,
)
from app.models import Customer, CustomerPage, Gender, HealthStatus
from app.repository import (
    CustomerFilters,
    count_customers,
    get_customer,
    list_customers,
)


LOGGER = logging.getLogger(__name__)


def get_connection(request: Request) -> Generator[sqlite3.Connection, None, None]:
    """Provide one request-scoped database connection."""
    connection = connect(request.app.state.database_path)
    try:
        yield connection
    finally:
        connection.close()


DatabaseConnection = Annotated[sqlite3.Connection, Depends(get_connection)]


def _validate_range(name: str, minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=422,
            detail=f"{name}_min cannot be greater than {name}_max",
        )


def create_app(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
) -> FastAPI:
    """Build an application instance, allowing isolated databases in tests."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialize_database(
            application.state.database_path,
            application.state.dataset_path,
        )
        yield

    application = FastAPI(
        title="Shopping Customer API",
        version="1.0.0",
        description=(
            "Read-only access to the shopping customer dataset with pagination, "
            "filters, and search."
        ),
        lifespan=lifespan,
    )
    application.state.database_path = Path(database_path)
    application.state.dataset_path = Path(dataset_path)

    @application.exception_handler(sqlite3.DatabaseError)
    async def database_exception_handler(
        request: Request, exc: sqlite3.DatabaseError
    ) -> JSONResponse:
        LOGGER.exception("Database error while handling %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "A database operation failed"},
        )

    @application.get("/health", response_model=HealthStatus, tags=["system"])
    def health(connection: DatabaseConnection) -> HealthStatus:
        return HealthStatus(status="ok", records=count_customers(connection))

    @application.get("/customers", response_model=CustomerPage, tags=["customers"])
    def customers(
        connection: DatabaseConnection,
        page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
        gender: Annotated[Gender | None, Query()] = None,
        age_min: Annotated[int | None, Query(ge=0, le=120)] = None,
        age_max: Annotated[int | None, Query(ge=0, le=120)] = None,
        income_min: Annotated[int | None, Query(ge=0)] = None,
        income_max: Annotated[int | None, Query(ge=0)] = None,
        score_min: Annotated[int | None, Query(ge=1, le=100)] = None,
        score_max: Annotated[int | None, Query(ge=1, le=100)] = None,
        search: Annotated[
            str | None,
            Query(
                min_length=1,
                max_length=50,
                description="Case-insensitive substring of customer ID or gender",
            ),
        ] = None,
    ) -> CustomerPage:
        _validate_range("age", age_min, age_max)
        _validate_range("income", income_min, income_max)
        _validate_range("score", score_min, score_max)

        filters = CustomerFilters(
            gender=gender.value if gender else None,
            age_min=age_min,
            age_max=age_max,
            income_min=income_min,
            income_max=income_max,
            score_min=score_min,
            score_max=score_max,
            search=search.strip() if search else None,
        )
        total = count_customers(connection, filters)
        rows = list_customers(
            connection,
            filters,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        return CustomerPage(
            items=[Customer.model_validate(dict(row)) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    @application.get(
        "/customers/{customer_id}", response_model=Customer, tags=["customers"]
    )
    def customer_by_id(
        connection: DatabaseConnection,
        customer_id: Annotated[
            str,
            ApiPath(pattern=r"^\d{4}$", description="Four-digit source customer ID"),
        ],
    ) -> Customer:
        row = get_customer(connection, customer_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer.model_validate(dict(row))

    return application


app = create_app()
