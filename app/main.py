from __future__ import annotations

import math
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path as PathParameter, Query, Request
from fastapi.responses import JSONResponse

from app.database import database_path_from_env, initialize_database
from app.models import CustomerPage, CustomerResponse, HealthResponse
from app.repository import customer_count, get_customer, list_customers


GenreFilter = Annotated[
    str | None,
    Query(
        pattern=r"(?i)^(male|female)$",
        description="Case-insensitive genre value from the source dataset.",
    ),
]


def _validate_range(
    label: str, minimum: int | None, maximum: int | None
) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=422,
            detail=f"{label} minimum cannot be greater than its maximum.",
        )


def create_app(database_path: Path | str | None = None) -> FastAPI:
    resolved_database_path = Path(database_path or database_path_from_env())

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(resolved_database_path)
        yield

    application = FastAPI(
        title="Shopping Customer API",
        version="1.0.0",
        description=(
            "Read-only REST API for exploring the Shopping_data.csv customer "
            "segmentation dataset."
        ),
        lifespan=lifespan,
    )
    application.state.database_path = resolved_database_path

    @application.exception_handler(sqlite3.Error)
    async def database_error_handler(_: Request, __: sqlite3.Error) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "The local database operation failed."},
        )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            database="ready",
            customer_count=customer_count(resolved_database_path),
        )

    @application.get(
        "/customers",
        response_model=CustomerPage,
        tags=["customers"],
        summary="List, filter, and search customers",
    )
    def customers(
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 25,
        genre: GenreFilter = None,
        min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        min_annual_income: Annotated[int | None, Query(ge=0)] = None,
        max_annual_income: Annotated[int | None, Query(ge=0)] = None,
        min_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        max_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        q: Annotated[
            str | None,
            Query(
                min_length=1,
                max_length=50,
                description="Case-insensitive partial match on customer ID or genre.",
            ),
        ] = None,
        sort_by: Literal[
            "customer_id", "age", "annual_income_k", "spending_score"
        ] = "customer_id",
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> CustomerPage:
        _validate_range("Age", min_age, max_age)
        _validate_range("Annual income", min_annual_income, max_annual_income)
        _validate_range(
            "Spending score", min_spending_score, max_spending_score
        )
        normalized_query = q.strip() if q else None
        if q is not None and not normalized_query:
            raise HTTPException(
                status_code=422, detail="Search query cannot contain only whitespace."
            )

        items, total = list_customers(
            resolved_database_path,
            page=page,
            page_size=page_size,
            genre=genre.title() if genre else None,
            min_age=min_age,
            max_age=max_age,
            min_annual_income=min_annual_income,
            max_annual_income=max_annual_income,
            min_spending_score=min_spending_score,
            max_spending_score=max_spending_score,
            query=normalized_query,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return CustomerPage(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size),
        )

    @application.get(
        "/customers/{customer_id}",
        response_model=CustomerResponse,
        tags=["customers"],
        summary="Get one customer",
    )
    def customer(
        customer_id: Annotated[
            str,
            PathParameter(
                pattern=r"^\d{4}$",
                description="Four-digit source customer identifier.",
            ),
        ]
    ) -> CustomerResponse:
        record = get_customer(resolved_database_path, customer_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Customer not found.")
        return CustomerResponse(**record)

    return application


app = create_app()
