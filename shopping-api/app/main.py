"""FastAPI application exposing the shopping (mall customers) dataset."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from . import __version__, crud
from .config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from .crud import CustomerFilters
from .database import get_db
from .schemas import (
    CustomerOut,
    Gender,
    PageMeta,
    PaginatedCustomers,
    SortField,
    SortOrder,
    StatsOut,
)

app = FastAPI(
    title="Shopping API",
    version=__version__,
    description=(
        "A small production-style REST API over the mall-customers shopping "
        "dataset. Supports listing, pagination, filtering, and search."
    ),
)


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """Return a helpful message when the database has not been initialised yet."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": (
                "Database is not available or not initialised. "
                "Run `python -m scripts.import_data` to create and populate it."
            )
        },
    )


def customer_filters(
    gender: Annotated[Gender | None, Query(description="Filter by gender")] = None,
    min_age: Annotated[int | None, Query(ge=0, le=120, description="Minimum age (inclusive)")] = None,
    max_age: Annotated[int | None, Query(ge=0, le=120, description="Maximum age (inclusive)")] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Minimum annual income in k$")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Maximum annual income in k$")] = None,
    min_spending: Annotated[int | None, Query(ge=1, le=100, description="Minimum spending score")] = None,
    max_spending: Annotated[int | None, Query(ge=1, le=100, description="Maximum spending score")] = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=50, description="Case-insensitive search over customer id and gender"),
    ] = None,
) -> CustomerFilters:
    """Build and validate the set of filters for the list endpoint."""

    def _check_range(low, high, label: str) -> None:
        if low is not None and high is not None and low > high:
            raise HTTPException(
                status_code=422,  # Unprocessable Content
                detail=f"min_{label} ({low}) cannot be greater than max_{label} ({high}).",
            )

    _check_range(min_age, max_age, "age")
    _check_range(min_income, max_income, "income")
    _check_range(min_spending, max_spending, "spending")

    return CustomerFilters(
        gender=gender.value if gender else None,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_spending=min_spending,
        max_spending=max_spending,
        search=search,
    )


@app.get("/", include_in_schema=False)
def root() -> dict:
    """Tiny landing payload pointing at the interactive docs."""
    return {
        "name": "Shopping API",
        "version": __version__,
        "docs": "/docs",
        "endpoints": ["/health", "/customers", "/customers/{customer_id}", "/stats"],
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}


@app.get(
    "/customers",
    response_model=PaginatedCustomers,
    tags=["customers"],
    summary="List customers with pagination, filtering and search",
)
def list_customers(
    filters: Annotated[CustomerFilters, Depends(customer_filters)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Page size")] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.customer_id,
    order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.asc,
) -> PaginatedCustomers:
    items, total = crud.list_customers(
        db,
        filters,
        limit=limit,
        offset=offset,
        sort_by=sort_by.value,
        order=order.value,
    )
    return PaginatedCustomers(
        meta=PageMeta(total=total, limit=limit, offset=offset, count=len(items)),
        items=[CustomerOut.model_validate(item) for item in items],
    )


@app.get(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    tags=["customers"],
    summary="Fetch a single customer by id",
    responses={404: {"description": "Customer not found"}},
)
def get_customer(
    customer_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerOut:
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{customer_id}' not found.",
        )
    return CustomerOut.model_validate(customer)


@app.get("/stats", response_model=StatsOut, tags=["meta"], summary="Dataset statistics")
def stats(db: Annotated[Session, Depends(get_db)]) -> StatsOut:
    return StatsOut.model_validate(crud.get_stats(db))
