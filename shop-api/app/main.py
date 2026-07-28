"""Shop API - a small REST service over the mall shopping dataset."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any, Iterator

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import queries
from .config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, get_settings
from .db import connect, is_initialised
from .models import (
    AgeBracket,
    Band,
    Customer,
    CustomerPage,
    ErrorResponse,
    Gender,
    Pagination,
    SortField,
    SortOrder,
    Stats,
)
from .queries import CustomerFilters

API_PREFIX = "/api/v1"

app = FastAPI(
    title="Shop API",
    version="1.0.0",
    description=(
        "Read-only REST API over the mall shopping dataset "
        "(200 customers: gender, age, annual income, spending score). "
        "Supports pagination, filtering, free-text search and aggregate statistics."
    ),
    responses={
        422: {"model": ErrorResponse, "description": "Invalid query parameters"},
        503: {"model": ErrorResponse, "description": "Database not initialised"},
    },
)


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------


def api_error(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> HTTPException:
    """Build an HTTPException that renders as the standard error envelope."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def _envelope(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or "request",
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_envelope("validation_error", "One or more query parameters are invalid.", details),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Wrap every HTTP error - ours and framework 404/405s - in one envelope."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        payload = _envelope(exc.detail["code"], exc.detail["message"], exc.detail.get("details"))
    else:
        payload = _envelope("http_error", str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)


@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(_: Request, exc: sqlite3.Error) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope("database_error", f"Database error: {exc.__class__.__name__}."),
    )


# --------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------


def get_db() -> Iterator[sqlite3.Connection]:
    """One SQLite connection per request, closed when the response is done."""
    settings = get_settings()
    conn = connect(settings.db_path)
    try:
        if not is_initialised(conn):
            raise api_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "database_not_initialised",
                f"No customer data found at {settings.db_path}. "
                "Run 'python -m app.importer' first.",
            )
        yield conn
    finally:
        conn.close()


DbConn = Annotated[sqlite3.Connection, Depends(get_db)]


def customer_filters(
    gender: Annotated[Gender | None, Query(description="Exact gender match.")] = None,
    min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Minimum annual income in k$.")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Maximum annual income in k$.")] = None,
    min_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    age_bracket: Annotated[AgeBracket | None, Query()] = None,
    income_band: Annotated[Band | None, Query(description="low <40k, medium 40-79k, high >=80k.")] = None,
    spending_tier: Annotated[Band | None, Query(description="low <35, medium 35-64, high >=65.")] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=64,
            description=(
                "Free-text search across customer_ref, gender, age_bracket, "
                "income_band and spending_tier."
            ),
        ),
    ] = None,
) -> CustomerFilters:
    """Collect and cross-validate listing filters.

    FastAPI handles per-parameter bounds; the pairwise min/max checks that it
    cannot express are done here and reported as 400 invalid_range.
    """
    ranges = (
        ("age", min_age, max_age),
        ("income", min_income, max_income),
        ("spending_score", min_spending_score, max_spending_score),
    )
    for name, low, high in ranges:
        if low is not None and high is not None and low > high:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                "invalid_range",
                f"min_{name} ({low}) cannot be greater than max_{name} ({high}).",
            )

    search = q.strip() if q else None
    return CustomerFilters(
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_spending_score=min_spending_score,
        max_spending_score=max_spending_score,
        age_bracket=age_bracket,
        income_band=income_band,
        spending_tier=spending_tier,
        q=search or None,
    )


Filters = Annotated[CustomerFilters, Depends(customer_filters)]


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.get("/", tags=["meta"], summary="Service information")
def root() -> dict[str, Any]:
    return {
        "service": "Shop API",
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": [
            f"{API_PREFIX}/customers",
            f"{API_PREFIX}/customers/{{customer_id}}",
            f"{API_PREFIX}/stats",
            "/health",
        ],
    }


@app.get("/health", tags=["meta"], summary="Liveness and data readiness")
def health() -> dict[str, Any]:
    """Never fails on missing data - it reports it, so it is usable as a probe."""
    settings = get_settings()
    conn = connect(settings.db_path)
    try:
        ready = is_initialised(conn)
        total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] if ready else 0
        last_import = None
        if ready:
            row = conn.execute(
                "SELECT source_file, rows_imported, imported_at FROM import_runs "
                "ORDER BY id DESC LIMIT 1"
            ).fetchone()
            last_import = dict(row) if row else None
    except sqlite3.Error:
        ready, total, last_import = False, 0, None
    finally:
        conn.close()

    return {
        "status": "ok" if ready else "degraded",
        "database": str(settings.db_path),
        "data_loaded": ready,
        "customers": total,
        "last_import": last_import,
    }


@app.get(
    f"{API_PREFIX}/customers",
    response_model=CustomerPage,
    tags=["customers"],
    summary="List customers with pagination, filtering and search",
    responses={400: {"model": ErrorResponse, "description": "Contradictory min/max range"}},
)
def list_customers(
    conn: DbConn,
    filters: Filters,
    page: Annotated[int, Query(ge=1, description="1-based page number.")] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    sort_by: Annotated[SortField, Query()] = SortField.id,
    order: Annotated[SortOrder, Query()] = SortOrder.asc,
) -> CustomerPage:
    total_items = queries.count_customers(conn, filters)
    total_pages = (total_items + page_size - 1) // page_size

    rows = queries.list_customers(
        conn,
        filters,
        limit=page_size,
        offset=(page - 1) * page_size,
        sort_by=sort_by,
        order=order,
    )

    return CustomerPage(
        data=[Customer(**dict(row)) for row in rows],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1 and total_items > 0,
        ),
        filters_applied=filters.as_dict(),
    )


@app.get(
    f"{API_PREFIX}/customers/{{customer_id}}",
    response_model=Customer,
    tags=["customers"],
    summary="Fetch a single customer by id",
    responses={404: {"model": ErrorResponse, "description": "No such customer"}},
)
def get_customer(
    conn: DbConn,
    customer_id: Annotated[int, Path(ge=1, description="Numeric id; '0007' and '7' both work.")],
) -> Customer:
    row = queries.get_customer(conn, customer_id)
    if row is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            "customer_not_found",
            f"No customer with id {customer_id}.",
        )
    return Customer(**dict(row))


@app.get(
    f"{API_PREFIX}/stats",
    response_model=Stats,
    tags=["customers"],
    summary="Aggregate statistics and segment breakdowns",
)
def get_stats(conn: DbConn) -> Stats:
    return Stats(**queries.stats(conn))
