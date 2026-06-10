from __future__ import annotations

import math
import sqlite3
from contextlib import asynccontextmanager, closing
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path as ApiPath, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import DEFAULT_CSV_PATH, DEFAULT_DB_PATH, connect, ensure_database
from app.repository import (
    CustomerFilters,
    get_customer,
    get_dataset_stats,
    list_customers,
)
from app.schemas import Customer, CustomerListResponse, DatasetStats


def _error_payload(code: str, message: str, details: object | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


def _validate_range(
    field_name: str,
    minimum: int | None,
    maximum: int | None,
) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} minimum cannot be greater than maximum",
        )


def _normalize_genre(genre: str | None) -> str | None:
    return genre.title() if genre else None


def _normalize_search(query: str | None) -> str | None:
    if query is None:
        return None
    cleaned = query.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="q cannot be blank")
    return cleaned


def create_app(
    db_path: Path | str | None = None,
    csv_path: Path | str | None = None,
) -> FastAPI:
    database_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    source_csv_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ensure_database(db_path=database_path, csv_path=source_csv_path)
        yield

    app = FastAPI(
        title="Shopping Customer API",
        version="0.1.0",
        description="REST API for exploring customer shopping segmentation data.",
        lifespan=lifespan,
    )
    app.state.db_path = database_path
    app.state.csv_path = source_csv_path

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "request_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(code=code, message=str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            {
                "location": list(error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                code="validation_error",
                message="Request validation failed",
                details=details,
            ),
        )

    @app.exception_handler(sqlite3.Error)
    async def sqlite_exception_handler(
        request: Request,
        exc: sqlite3.Error,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                code="database_error",
                message="The database could not process the request",
            ),
        )

    @app.get("/health", tags=["system"])
    def health(request: Request) -> dict[str, object]:
        with closing(connect(request.app.state.db_path)) as connection:
            total_records = get_dataset_stats(connection)["total_records"]
        return {"status": "ok", "records": total_records}

    @app.get("/customers", response_model=CustomerListResponse, tags=["customers"])
    def customers(
        request: Request,
        page: Annotated[int, Query(ge=1, description="One-based page number.")] = 1,
        per_page: Annotated[
            int,
            Query(ge=1, le=100, description="Number of records per page."),
        ] = 25,
        genre: Annotated[
            str | None,
            Query(pattern="^(Male|Female|male|female)$", description="Filter by genre."),
        ] = None,
        min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        min_income: Annotated[int | None, Query(ge=0)] = None,
        max_income: Annotated[int | None, Query(ge=0)] = None,
        min_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        max_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        q: Annotated[
            str | None,
            Query(
                min_length=1,
                max_length=50,
                description="Case-insensitive search across id, genre, age, income, and score.",
            ),
        ] = None,
        sort_by: Annotated[
            Literal["customer_id", "age", "annual_income_k", "spending_score"],
            Query(description="Field used to order the page."),
        ] = "customer_id",
        sort_order: Annotated[
            Literal["asc", "desc"],
            Query(description="Sort direction."),
        ] = "asc",
    ) -> CustomerListResponse:
        _validate_range("age", min_age, max_age)
        _validate_range("income", min_income, max_income)
        _validate_range("spending score", min_spending_score, max_spending_score)

        filters = CustomerFilters(
            genre=_normalize_genre(genre),
            min_age=min_age,
            max_age=max_age,
            min_income=min_income,
            max_income=max_income,
            min_spending_score=min_spending_score,
            max_spending_score=max_spending_score,
            q=_normalize_search(q),
        )
        with closing(connect(request.app.state.db_path)) as connection:
            items, total = list_customers(
                connection=connection,
                filters=filters,
                page=page,
                per_page=per_page,
                sort_by=sort_by,
                sort_order=sort_order,
            )

        total_pages = math.ceil(total / per_page) if total else 0
        return CustomerListResponse(
            data=[Customer(**item) for item in items],
            pagination={
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        )

    @app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
    def customer_by_id(
        request: Request,
        customer_id: Annotated[
            str,
            ApiPath(pattern="^[0-9]{4}$", description="Four digit customer id."),
        ],
    ) -> Customer:
        with closing(connect(request.app.state.db_path)) as connection:
            customer = get_customer(connection, customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer(**customer)

    @app.get("/stats", response_model=DatasetStats, tags=["customers"])
    def stats(request: Request) -> DatasetStats:
        with closing(connect(request.app.state.db_path)) as connection:
            return DatasetStats(**get_dataset_stats(connection))

    return app


app = create_app()

