"""FastAPI application exposing the shopping (mall customers) dataset.

Endpoints
---------
GET /health                  Liveness probe.
GET /customers               List customers with pagination, filtering, search.
GET /customers/{id}          Fetch a single customer by id.
GET /customers/stats/summary Aggregate statistics over the filtered dataset.
"""

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import get_db

app = FastAPI(
    title="Shopping Dataset API",
    description=(
        "A small production-style REST API over the mall shopping dataset "
        "(customer demographics, annual income and spending score)."
    ),
    version="1.0.0",
)


def _filter_params(
    genre: Optional[str] = Query(
        None, description="Filter by gender (Male/Female, case-insensitive)"
    ),
    min_age: Optional[int] = Query(None, ge=0, description="Minimum age (inclusive)"),
    max_age: Optional[int] = Query(None, ge=0, description="Maximum age (inclusive)"),
    min_income: Optional[int] = Query(
        None, ge=0, description="Minimum annual income k$ (inclusive)"
    ),
    max_income: Optional[int] = Query(
        None, ge=0, description="Maximum annual income k$ (inclusive)"
    ),
    min_spending_score: Optional[int] = Query(
        None, ge=1, le=100, description="Minimum spending score (inclusive)"
    ),
    max_spending_score: Optional[int] = Query(
        None, ge=1, le=100, description="Maximum spending score (inclusive)"
    ),
    search: Optional[str] = Query(
        None, description="Free-text search across genre and customer id"
    ),
) -> dict:
    """Collect and cross-validate the shared filter query parameters."""
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(422, "min_age cannot be greater than max_age")
    if min_income is not None and max_income is not None and min_income > max_income:
        raise HTTPException(422, "min_income cannot be greater than max_income")
    if (
        min_spending_score is not None
        and max_spending_score is not None
        and min_spending_score > max_spending_score
    ):
        raise HTTPException(
            422, "min_spending_score cannot be greater than max_spending_score"
        )
    if genre is not None and genre.lower() not in {"male", "female"}:
        raise HTTPException(422, "genre must be 'Male' or 'Female'")

    return {
        "genre": genre,
        "min_age": min_age,
        "max_age": max_age,
        "min_income": min_income,
        "max_income": max_income,
        "min_spending_score": min_spending_score,
        "max_spending_score": max_spending_score,
        "search": search,
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}


@app.get("/customers", response_model=schemas.PaginatedCustomers, tags=["customers"])
def list_customers(
    limit: int = Query(20, ge=1, le=200, description="Page size (1-200)"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    sort_by: str = Query(
        "customer_id",
        pattern="^(customer_id|age|annual_income_k|spending_score)$",
        description="Field to sort by",
    ),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction"),
    filters: dict = Depends(_filter_params),
    db: Session = Depends(get_db),
):
    """List customers with pagination, filtering, search and sorting."""
    total, items = crud.list_customers(
        db, limit=limit, offset=offset, sort_by=sort_by, order=order, **filters
    )
    return schemas.PaginatedCustomers(
        total=total, limit=limit, offset=offset, count=len(items), items=items
    )


@app.get(
    "/customers/stats/summary", response_model=schemas.StatsOut, tags=["customers"]
)
def customer_stats(
    filters: dict = Depends(_filter_params),
    db: Session = Depends(get_db),
):
    """Aggregate statistics over the (optionally filtered) dataset."""
    return crud.get_stats(db, **filters)


@app.get(
    "/customers/{customer_id}", response_model=schemas.CustomerOut, tags=["customers"]
)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Fetch a single customer by id, or 404 if it does not exist."""
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(404, f"Customer {customer_id} not found")
    return customer
