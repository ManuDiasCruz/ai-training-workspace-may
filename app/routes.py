"""API route definitions for the customers resource."""

from __future__ import annotations

import math
import sqlite3
from enum import Enum
from typing import Annotated, Iterator

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from . import repository
from .database import connect
from .repository import CustomerFilters
from .schemas import Customer, CustomerListResponse, ErrorResponse, Pagination, StatsResponse

router = APIRouter(prefix="/api/v1", tags=["customers"])

VALID_GENRES = ("Male", "Female")


def get_db() -> Iterator[sqlite3.Connection]:
    """Yield a per-request database connection."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


class SortField(str, Enum):
    customer_id = "customer_id"
    genre = "genre"
    age = "age"
    annual_income_k = "annual_income_k"
    spending_score = "spending_score"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


def _normalize_genre(genre: str | None) -> str | None:
    """Accept any capitalization of Male/Female, reject anything else."""
    if genre is None:
        return None
    normalized = genre.strip().capitalize()
    if normalized not in VALID_GENRES:
        raise HTTPException(
            status_code=422,
            detail=f"genre must be one of {list(VALID_GENRES)} (case-insensitive), got {genre!r}",
        )
    return normalized


def _check_range(name: str, low: int | None, high: int | None) -> None:
    if low is not None and high is not None and low > high:
        raise HTTPException(
            status_code=400,
            detail=f"min_{name} ({low}) cannot be greater than max_{name} ({high})",
        )


@router.get(
    "/customers",
    response_model=CustomerListResponse,
    summary="List customers with pagination, filtering, search and sorting",
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def list_customers(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page (max 100)")] = 20,
    genre: Annotated[str | None, Query(description="Filter by genre: Male or Female (case-insensitive)")] = None,
    min_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Minimum annual income (k$)")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Maximum annual income (k$)")] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100, description="Minimum spending score")] = None,
    max_score: Annotated[int | None, Query(ge=1, le=100, description="Maximum spending score")] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=40,
            description="Search: substring of the zero-padded customer ID (e.g. '0042') or genre prefix (e.g. 'fem')",
        ),
    ] = None,
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.customer_id,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.asc,
) -> CustomerListResponse:
    _check_range("age", min_age, max_age)
    _check_range("income", min_income, max_income)
    _check_range("score", min_score, max_score)

    filters = CustomerFilters(
        genre=_normalize_genre(genre),
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_score=min_score,
        max_score=max_score,
        q=q,
    )

    total_items = repository.count_customers(db, filters)
    rows = repository.list_customers(
        db,
        filters,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    total_pages = math.ceil(total_items / page_size) if total_items else 0

    return CustomerListResponse(
        items=[Customer(**dict(row)) for row in rows],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1 and total_items > 0,
        ),
    )


# NOTE: declared before /customers/{customer_id} so "stats" is not captured
# as a path parameter.
@router.get(
    "/customers/stats",
    response_model=StatsResponse,
    summary="Aggregate statistics over the whole dataset",
)
def customer_stats(db: Annotated[sqlite3.Connection, Depends(get_db)]) -> StatsResponse:
    return StatsResponse(**repository.get_stats(db))


@router.get(
    "/customers/{customer_id}",
    response_model=Customer,
    summary="Fetch a single customer by ID",
    responses={404: {"model": ErrorResponse}},
)
def get_customer(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    customer_id: Annotated[int, Path(ge=1, description="Numeric customer ID (1-200 in the source data)")],
) -> Customer:
    row = repository.get_customer(db, customer_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return Customer(**dict(row))
