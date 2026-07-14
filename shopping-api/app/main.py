"""FastAPI application exposing the shopping (mall customers) dataset."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import __version__, crud
from .config import CSV_PATH
from .database import SessionLocal, get_db, init_db
from .importer import DatasetError, seed_if_empty
from .schemas import (
    CustomerOut,
    Gender,
    PageMeta,
    PaginatedCustomers,
    SortField,
    SortOrder,
    Stats,
)

logger = logging.getLogger("shopping_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup and optionally seed the DB from the CSV."""
    init_db()
    if os.environ.get("SHOPPING_AUTO_SEED", "1") == "1":
        db = SessionLocal()
        try:
            imported = seed_if_empty(db, CSV_PATH)
            if imported:
                logger.info("Seeded %d customers from %s", imported, CSV_PATH)
        except DatasetError as exc:
            # Don't crash the app if the CSV is missing; endpoints still work
            # (returning empty results) and the importer can be run manually.
            logger.warning("Auto-seed skipped: %s", exc)
        finally:
            db.close()
    yield


app = FastAPI(
    title="Shopping API",
    version=__version__,
    description=(
        "A small REST API over the mall-customers shopping dataset. "
        "Supports listing, pagination, filtering, and basic search."
    ),
    lifespan=lifespan,
)


def customer_filters(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page (max 100)"),
    gender: Gender | None = Query(None, description="Filter by gender (Male/Female)"),
    min_age: int | None = Query(None, ge=0, le=120),
    max_age: int | None = Query(None, ge=0, le=120),
    min_income: int | None = Query(None, ge=0, description="Minimum annual income (k$)"),
    max_income: int | None = Query(None, ge=0, description="Maximum annual income (k$)"),
    min_spending_score: int | None = Query(None, ge=1, le=100),
    max_spending_score: int | None = Query(None, ge=1, le=100),
    search: str | None = Query(
        None,
        min_length=1,
        max_length=50,
        description="Substring match on customer id or gender",
    ),
    sort_by: SortField = Query(SortField.customer_id),
    order: SortOrder = Query(SortOrder.asc),
) -> crud.CustomerFilters:
    """Parse, range-check and cross-validate list query parameters.

    FastAPI/Pydantic enforce per-field ranges (returning 422). Here we add the
    cross-field rules that a single field constraint cannot express.
    """
    def ensure_range(lo, hi, name: str) -> None:
        if lo is not None and hi is not None and lo > hi:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"min_{name} ({lo}) cannot be greater than max_{name} ({hi})",
            )

    ensure_range(min_age, max_age, "age")
    ensure_range(min_income, max_income, "income")
    ensure_range(min_spending_score, max_spending_score, "spending_score")

    return crud.CustomerFilters(
        page=page,
        page_size=page_size,
        gender=gender.value if gender else None,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_spending_score=min_spending_score,
        max_spending_score=max_spending_score,
        search=search,
        sort_by=sort_by,
        order=order,
    )


@app.get("/", tags=["meta"], summary="API index")
def root() -> dict:
    """Return a short description and the list of available endpoints."""
    return {
        "name": "Shopping API",
        "version": __version__,
        "docs": "/docs",
        "endpoints": ["/health", "/customers", "/customers/{customer_id}", "/stats"],
    }


@app.get("/health", tags=["meta"], summary="Health check")
def health(db: Session = Depends(get_db)) -> dict:
    """Report service health and how many records are currently loaded."""
    total = crud.count_customers(db, crud.CustomerFilters())
    return {"status": "ok", "records": total}


@app.get(
    "/customers",
    response_model=PaginatedCustomers,
    tags=["customers"],
    summary="List customers with pagination, filtering and search",
)
def list_customers(
    filters: crud.CustomerFilters = Depends(customer_filters),
    db: Session = Depends(get_db),
) -> PaginatedCustomers:
    total = crud.count_customers(db, filters)
    rows = crud.list_customers(db, filters)
    total_pages = (total + filters.page_size - 1) // filters.page_size
    return PaginatedCustomers(
        meta=PageMeta(
            page=filters.page,
            page_size=filters.page_size,
            total=total,
            total_pages=total_pages,
        ),
        items=[CustomerOut.model_validate(r) for r in rows],
    )


@app.get(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    tags=["customers"],
    summary="Get a single customer by id",
    responses={404: {"description": "Customer not found"}},
)
def get_customer(customer_id: str, db: Session = Depends(get_db)) -> CustomerOut:
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id!r} not found",
        )
    return CustomerOut.model_validate(customer)


@app.get("/stats", response_model=Stats, tags=["customers"], summary="Aggregate dataset statistics")
def stats(db: Session = Depends(get_db)) -> Stats:
    return Stats.model_validate(crud.get_stats(db))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # pragma: no cover - safety net
    """Return a uniform 500 body instead of leaking internals."""
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
