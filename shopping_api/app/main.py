from __future__ import annotations

import math
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path as ApiPath, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import DEFAULT_DB_PATH, connect, initialize_database


class Customer(BaseModel):
    customer_id: str
    gender: str
    age: int
    annual_income_k: int
    spending_score: int


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool


def _assert_valid_range(name: str, lower: int | None, upper: int | None) -> None:
    if lower is not None and upper is not None and lower > upper:
        raise HTTPException(
            status_code=422,
            detail=f"{name} minimum cannot be greater than the maximum",
        )


def create_app(db_path: str | Path | None = None) -> FastAPI:
    selected_db_path = Path(
        db_path or os.environ.get("SHOPPING_DB_PATH", str(DEFAULT_DB_PATH))
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(selected_db_path)
        yield

    application = FastAPI(
        title="Shopping Dataset API",
        description="Read-only customer shopping records backed by SQLite.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.db_path = selected_db_path

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid request parameters", "errors": exc.errors()},
        )

    @application.get("/", tags=["service"])
    def root() -> dict[str, str]:
        return {
            "name": "Shopping Dataset API",
            "version": "1.0.0",
            "docs": "/docs",
        }

    @application.get("/health", tags=["service"])
    def health() -> dict[str, int | str]:
        with connect(application.state.db_path) as connection:
            total = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        return {"status": "ok", "database": "connected", "records": total}

    @application.get("/customers", response_model=CustomerPage, tags=["customers"])
    def list_customers(
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
        gender: Literal["Male", "Female"] | None = None,
        min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        min_income: Annotated[int | None, Query(ge=0)] = None,
        max_income: Annotated[int | None, Query(ge=0)] = None,
        min_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        max_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    ) -> CustomerPage:
        _assert_valid_range("age", min_age, max_age)
        _assert_valid_range("income", min_income, max_income)
        _assert_valid_range(
            "spending score", min_spending_score, max_spending_score
        )

        conditions: list[str] = []
        parameters: list[str | int] = []
        filters = [
            ("gender = ?", gender),
            ("age >= ?", min_age),
            ("age <= ?", max_age),
            ("annual_income_k >= ?", min_income),
            ("annual_income_k <= ?", max_income),
            ("spending_score >= ?", min_spending_score),
            ("spending_score <= ?", max_spending_score),
        ]
        for condition, value in filters:
            if value is not None:
                conditions.append(condition)
                parameters.append(value)
        if search is not None:
            conditions.append("(LOWER(customer_id) LIKE ? OR LOWER(gender) LIKE ?)")
            pattern = f"%{search.lower()}%"
            parameters.extend([pattern, pattern])

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (page - 1) * page_size
        with connect(application.state.db_path) as connection:
            total = connection.execute(
                f"SELECT COUNT(*) FROM customers{where_clause}", parameters
            ).fetchone()[0]
            rows = connection.execute(
                "SELECT customer_id, gender, age, annual_income_k, spending_score "
                f"FROM customers{where_clause} ORDER BY customer_id LIMIT ? OFFSET ?",
                [*parameters, page_size, offset],
            ).fetchall()

        total_pages = math.ceil(total / page_size) if total else 0
        return CustomerPage(
            items=[Customer(**dict(row)) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
        )

    @application.get(
        "/customers/{customer_id}", response_model=Customer, tags=["customers"]
    )
    def get_customer(
        customer_id: Annotated[str, ApiPath(pattern=r"^\d{4}$")],
    ) -> Customer:
        with connect(application.state.db_path) as connection:
            row = connection.execute(
                """
                SELECT customer_id, gender, age, annual_income_k, spending_score
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer(**dict(row))

    return application


app = create_app()

