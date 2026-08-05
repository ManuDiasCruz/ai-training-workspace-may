"""FastAPI application exposing the shopping customer dataset."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path as ApiPath, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_database_path
from app.database import connect, initialize_database
from app.repository import CustomerFilters, get_customer, list_customers
from app.schemas import Customer, CustomerPage, Gender, HealthResponse


LOGGER = logging.getLogger(__name__)


def _validate_range(name: str, minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_range",
                "message": f"min_{name} cannot exceed max_{name}.",
            },
        )


def create_app(database_path: str | Path | None = None) -> FastAPI:
    resolved_database_path = Path(database_path or get_database_path())

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialize_database(application.state.database_path)
        yield

    application = FastAPI(
        title="Shopping Customer API",
        description="Read-only access to customer income and spending-score data.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.database_path = resolved_database_path

    @application.exception_handler(RequestValidationError)
    async def request_validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, dict):
            error = exc.detail
        else:
            error = {
                "code": "not_found" if exc.status_code == 404 else "http_error",
                "message": str(exc.detail),
            }
        return JSONResponse(status_code=exc.status_code, content={"error": error})

    @application.exception_handler(sqlite3.Error)
    async def database_exception_handler(
        _request: Request, exc: sqlite3.Error
    ) -> JSONResponse:
        LOGGER.exception("Database operation failed", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "database_error",
                    "message": "The database operation could not be completed.",
                }
            },
        )

    @application.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {
            "name": "Shopping Customer API",
            "documentation": "/docs",
            "health": "/health",
        }

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health(request: Request) -> HealthResponse:
        with connect(request.app.state.database_path) as connection:
            connection.execute("SELECT 1").fetchone()
        return HealthResponse(status="ok", database="reachable")

    @application.get("/customers", response_model=CustomerPage, tags=["customers"])
    def customers(
        request: Request,
        page: Annotated[int, Query(ge=1, description="One-based page number")] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
        gender: Annotated[Gender | None, Query()] = None,
        min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        min_annual_income: Annotated[int | None, Query(ge=0)] = None,
        max_annual_income: Annotated[int | None, Query(ge=0)] = None,
        min_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        max_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        q: Annotated[
            str | None,
            Query(min_length=1, max_length=50, description="Customer ID or gender text"),
        ] = None,
    ) -> CustomerPage:
        if q is not None:
            q = q.strip()
            if not q:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": "invalid_search",
                        "message": "q must contain at least one non-space character.",
                    },
                )
        _validate_range("age", min_age, max_age)
        _validate_range(
            "annual_income", min_annual_income, max_annual_income
        )
        _validate_range(
            "spending_score", min_spending_score, max_spending_score
        )

        items, total = list_customers(
            request.app.state.database_path,
            CustomerFilters(
                gender=gender,
                min_age=min_age,
                max_age=max_age,
                min_annual_income=min_annual_income,
                max_annual_income=max_annual_income,
                min_spending_score=min_spending_score,
                max_spending_score=max_spending_score,
                search=q,
            ),
            page=page,
            page_size=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total else 0
        return CustomerPage(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @application.get(
        "/customers/{customer_id}", response_model=Customer, tags=["customers"]
    )
    def customer(
        request: Request,
        customer_id: Annotated[
            str,
            ApiPath(pattern=r"^\d{4}$", description="Four-digit customer ID"),
        ],
    ) -> Customer:
        record = get_customer(request.app.state.database_path, customer_id)
        if record is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail={
                    "code": "customer_not_found",
                    "message": f"Customer {customer_id} was not found.",
                },
            )
        return Customer(**record)

    return application


app = create_app()
