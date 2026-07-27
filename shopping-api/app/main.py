"""FastAPI application for browsing the shopping customer snapshot."""

from __future__ import annotations

import logging
import math
import sqlite3
from collections.abc import Generator
from enum import Enum
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from app.db import database_path, open_readonly_database
from app.models import Customer, CustomerPage, HealthResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shopping Customer API",
    version="1.0.0",
    description="Read-only access to the imported shopping customer dataset.",
)


class GenderFilter(str, Enum):
    male = "male"
    female = "female"


def get_connection() -> Generator[sqlite3.Connection, None, None]:
    try:
        connection = open_readonly_database(database_path())
    except (FileNotFoundError, sqlite3.Error) as exc:
        logger.warning("Could not open shopping database: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Run the import command before starting the API.",
        ) from exc
    try:
        yield connection
    finally:
        connection.close()


Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@app.exception_handler(sqlite3.Error)
async def database_error_handler(request: Request, exc: sqlite3.Error) -> JSONResponse:
    logger.exception("Database query failed for %s", request.url.path, exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Database query failed."})


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health(connection: Connection) -> HealthResponse:
    count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return HealthResponse(status="ok", records=count)


def validate_range(name: str, minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(status_code=422, detail=f"min_{name} must be less than or equal to max_{name}")


def escape_like(value: str) -> str:
    """Treat SQL LIKE metacharacters in user search text as literal characters."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
def list_customers(
    connection: Connection,
    page: Annotated[int, Query(ge=1, le=1_000_000, description="One-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Records per page (maximum 100)")] = 20,
    gender: Annotated[GenderFilter | None, Query(description="Exact, case-insensitive gender filter")] = None,
    min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Minimum annual income in k$")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Maximum annual income in k$")] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=50, description="Partial customer ID or gender search")] = None,
) -> CustomerPage:
    validate_range("age", min_age, max_age)
    validate_range("income", min_income, max_income)
    validate_range("score", min_score, max_score)

    clauses: list[str] = []
    parameters: list[str | int] = []
    if gender is not None:
        clauses.append("gender = ? COLLATE NOCASE")
        parameters.append(gender.value)
    for column, minimum, maximum in (
        ("age", min_age, max_age),
        ("annual_income_k", min_income, max_income),
        ("spending_score", min_score, max_score),
    ):
        if minimum is not None:
            clauses.append(f"{column} >= ?")
            parameters.append(minimum)
        if maximum is not None:
            clauses.append(f"{column} <= ?")
            parameters.append(maximum)
    if q is not None:
        search = q.strip()
        if not search:
            raise HTTPException(status_code=422, detail="q must contain a non-whitespace character")
        pattern = f"%{escape_like(search)}%"
        clauses.append("(customer_id LIKE ? ESCAPE '\\' OR gender LIKE ? ESCAPE '\\')")
        parameters.extend((pattern, pattern))

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    total = connection.execute(f"SELECT COUNT(*) FROM customers {where}", parameters).fetchone()[0]
    rows = connection.execute(
        f"""SELECT customer_id, gender, age, annual_income_k, spending_score
            FROM customers {where}
            ORDER BY customer_id
            LIMIT ? OFFSET ?""",
        [*parameters, page_size, (page - 1) * page_size],
    ).fetchall()
    total_pages = math.ceil(total / page_size)
    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        next_page=page + 1 if page < total_pages else None,
        previous_page=page - 1 if page > 1 else None,
    )


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
def get_customer(
    customer_id: Annotated[str, Path(pattern=r"^\d{4}$", description="Four-digit customer ID")],
    connection: Connection,
) -> Customer:
    row = connection.execute(
        """SELECT customer_id, gender, age, annual_income_k, spending_score
           FROM customers WHERE customer_id = ?""",
        (customer_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**dict(row))
