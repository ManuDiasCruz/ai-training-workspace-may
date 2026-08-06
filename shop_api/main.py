"""FastAPI application exposing the shopping customer dataset."""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from fastapi.responses import JSONResponse

from shop_api import __version__
from shop_api.database import connect, get_database_path
from shop_api.schemas import (
    Customer,
    CustomerPage,
    DatasetStatistics,
    Gender,
    HealthStatus,
    NumericSummary,
    Pagination,
)


app = FastAPI(
    title="Shopping Customer API",
    description=(
        "A read-only, SQLite-backed API for exploring the 200-customer "
        "shopping behavior dataset."
    ),
    version=__version__,
)


@app.exception_handler(sqlite3.Error)
async def handle_database_error(
    _request: Request,
    _exception: sqlite3.Error,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": (
                "The shopping database is unavailable or invalid. "
                "Run python -m shop_api.import_data before starting the API."
            )
        },
    )


def get_connection() -> Generator[sqlite3.Connection, None, None]:
    database_path = get_database_path()
    if not database_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The shopping database has not been initialized. "
                "Run python -m shop_api.import_data first."
            ),
        )

    connection = connect(database_path)
    try:
        yield connection
    finally:
        connection.close()


DatabaseConnection = Annotated[sqlite3.Connection, Depends(get_connection)]


def validate_range(
    minimum: int | None,
    maximum: int | None,
    *,
    minimum_name: str,
    maximum_name: str,
) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{minimum_name} cannot be greater than {maximum_name}.",
        )


def literal_like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@app.get("/health", response_model=HealthStatus, tags=["Operations"])
def health_check(connection: DatabaseConnection) -> HealthStatus:
    row = connection.execute("SELECT COUNT(*) AS total FROM customers").fetchone()
    return HealthStatus(status="ok", database="connected", customer_count=row["total"])


@app.get("/customers", response_model=CustomerPage, tags=["Customers"])
def list_customers(
    connection: DatabaseConnection,
    page: Annotated[int, Query(ge=1, description="One-based result page.")] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100, description="Customers per page, up to 100."),
    ] = 20,
    gender: Gender | None = None,
    min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0)] = None,
    max_income: Annotated[int | None, Query(ge=0)] = None,
    min_spending_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    max_spending_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="Case-insensitive literal search of customer ID and gender.",
        ),
    ] = None,
) -> CustomerPage:
    validate_range(min_age, max_age, minimum_name="min_age", maximum_name="max_age")
    validate_range(
        min_income,
        max_income,
        minimum_name="min_income",
        maximum_name="max_income",
    )
    validate_range(
        min_spending_score,
        max_spending_score,
        minimum_name="min_spending_score",
        maximum_name="max_spending_score",
    )

    conditions: list[str] = []
    parameters: list[str | int] = []

    if gender is not None:
        conditions.append("gender = ?")
        parameters.append(gender.value.capitalize())

    for column, minimum, maximum in (
        ("age", min_age, max_age),
        ("annual_income_k_usd", min_income, max_income),
        ("spending_score", min_spending_score, max_spending_score),
    ):
        if minimum is not None:
            conditions.append(f"{column} >= ?")
            parameters.append(minimum)
        if maximum is not None:
            conditions.append(f"{column} <= ?")
            parameters.append(maximum)

    if q is not None:
        pattern = literal_like_pattern(q)
        conditions.append(
            "(customer_id LIKE ? ESCAPE '\\' COLLATE NOCASE "
            "OR gender LIKE ? ESCAPE '\\' COLLATE NOCASE)"
        )
        parameters.extend((pattern, pattern))

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    total = connection.execute(
        f"SELECT COUNT(*) AS total FROM customers{where_clause}",
        parameters,
    ).fetchone()["total"]
    offset = (page - 1) * page_size
    rows = connection.execute(
        (
            "SELECT customer_id, gender, age, annual_income_k_usd, spending_score "
            f"FROM customers{where_clause} ORDER BY customer_id LIMIT ? OFFSET ?"
        ),
        [*parameters, page_size, offset],
    ).fetchall()

    total_pages = math.ceil(total / page_size) if total else 0
    return CustomerPage(
        items=[Customer.model_validate(dict(row)) for row in rows],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1 and total > 0,
        ),
    )


@app.get("/customers/{customer_id}", response_model=Customer, tags=["Customers"])
def get_customer(
    customer_id: Annotated[
        str,
        Path(pattern=r"^[0-9]{4}$", description="Four-digit customer identifier."),
    ],
    connection: DatabaseConnection,
) -> Customer:
    row = connection.execute(
        """
        SELECT customer_id, gender, age, annual_income_k_usd, spending_score
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id!r} was not found.",
        )

    return Customer.model_validate(dict(row))


@app.get("/stats", response_model=DatasetStatistics, tags=["Analytics"])
def get_statistics(connection: DatabaseConnection) -> DatasetStatistics:
    summary = connection.execute(
        """
        SELECT
            COUNT(*) AS total_customers,
            MIN(age) AS min_age,
            MAX(age) AS max_age,
            ROUND(AVG(age), 2) AS avg_age,
            MIN(annual_income_k_usd) AS min_income,
            MAX(annual_income_k_usd) AS max_income,
            ROUND(AVG(annual_income_k_usd), 2) AS avg_income,
            MIN(spending_score) AS min_score,
            MAX(spending_score) AS max_score,
            ROUND(AVG(spending_score), 2) AS avg_score
        FROM customers
        """
    ).fetchone()

    if not summary["total_customers"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The shopping database does not contain any imported customers.",
        )

    genders = connection.execute(
        "SELECT gender, COUNT(*) AS total FROM customers GROUP BY gender ORDER BY gender"
    ).fetchall()

    return DatasetStatistics(
        total_customers=summary["total_customers"],
        gender_breakdown={row["gender"]: row["total"] for row in genders},
        age=NumericSummary(
            minimum=summary["min_age"],
            maximum=summary["max_age"],
            average=summary["avg_age"],
        ),
        annual_income_k_usd=NumericSummary(
            minimum=summary["min_income"],
            maximum=summary["max_income"],
            average=summary["avg_income"],
        ),
        spending_score=NumericSummary(
            minimum=summary["min_score"],
            maximum=summary["max_score"],
            average=summary["avg_score"],
        ),
    )

