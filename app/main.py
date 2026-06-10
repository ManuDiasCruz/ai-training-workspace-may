"""FastAPI application exposing the shopping dataset over REST."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from math import ceil

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config, crud, models  # noqa: F401  (models import registers tables)
from app.database import Base, SessionLocal, engine, get_db
from app.schemas import (
    CustomerListResponse,
    CustomerOut,
    ErrorResponse,
    Gender,
    HealthResponse,
    PaginationMeta,
    SortField,
    SortOrder,
    StatsResponse,
)
from app.seed import seed_database

logger = logging.getLogger("shopping_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the schema exists and (optionally) auto-seed an empty database."""
    Base.metadata.create_all(bind=engine)
    if config.AUTO_SEED:
        with SessionLocal() as session:
            if crud.count_customers(session) == 0:
                try:
                    inserted = seed_database(session, config.DATASET_PATH)
                    logger.info("Auto-seeded %d customers on startup.", inserted)
                except FileNotFoundError:
                    logger.warning(
                        "AUTO_SEED is on but dataset %s was not found; "
                        "the database is empty.",
                        config.DATASET_PATH,
                    )
    yield


app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION,
    lifespan=lifespan,
)


# --------------------------------------------------------------------------- #
# Error handling: return a consistent {"error": {...}} envelope everywhere.
# --------------------------------------------------------------------------- #
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "status": 422,
                "message": "Request validation failed.",
                "details": jsonable_encoder(exc.errors()),
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"status": exc.status_code, "message": exc.detail}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):  # pragma: no cover
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"error": {"status": 500, "message": "Internal server error."}},
    )


# --------------------------------------------------------------------------- #
# Shared query-parameter dependency (filtering + cross-field validation).
# --------------------------------------------------------------------------- #
def _ensure_range(name: str, low: int | None, high: int | None) -> None:
    if low is not None and high is not None and low > high:
        raise HTTPException(
            status_code=422,
            detail=f"min_{name} ({low}) must be less than or equal to max_{name} ({high}).",
        )


def customer_filters(
    gender: Gender | None = Query(None, description="Exact gender match (Male or Female)."),
    min_age: int | None = Query(None, ge=0, le=120, description="Minimum age, inclusive."),
    max_age: int | None = Query(None, ge=0, le=120, description="Maximum age, inclusive."),
    min_income: int | None = Query(None, ge=0, description="Minimum annual income in k$."),
    max_income: int | None = Query(None, ge=0, description="Maximum annual income in k$."),
    min_spending_score: int | None = Query(
        None, ge=1, le=100, description="Minimum spending score (1-100)."
    ),
    max_spending_score: int | None = Query(
        None, ge=1, le=100, description="Maximum spending score (1-100)."
    ),
    search: str | None = Query(
        None,
        min_length=1,
        max_length=50,
        description="Case-insensitive gender match, or an exact customer ID when numeric.",
    ),
) -> crud.CustomerFilters:
    _ensure_range("age", min_age, max_age)
    _ensure_range("income", min_income, max_income)
    _ensure_range("spending_score", min_spending_score, max_spending_score)
    return crud.CustomerFilters(
        gender=gender.value if gender else None,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_spending_score=min_spending_score,
        max_spending_score=max_spending_score,
        search=search,
    )


# --------------------------------------------------------------------------- #
# Meta endpoints
# --------------------------------------------------------------------------- #
@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "name": config.API_TITLE,
        "version": config.API_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health(db: Session = Depends(get_db)) -> HealthResponse:
    return HealthResponse(status="ok", customers_loaded=crud.count_customers(db))


# --------------------------------------------------------------------------- #
# Customer endpoints (versioned)
# --------------------------------------------------------------------------- #
router = APIRouter(prefix="/api/v1", tags=["customers"])


@router.get(
    "/customers",
    response_model=CustomerListResponse,
    summary="List customers with pagination, filtering, search and sorting.",
)
def list_customers(
    filters: crud.CustomerFilters = Depends(customer_filters),
    page: int = Query(1, ge=1, description="1-based page number."),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)."),
    sort_by: SortField = Query(SortField.customer_id, description="Field to sort by."),
    order: SortOrder = Query(SortOrder.asc, description="Sort direction."),
    db: Session = Depends(get_db),
) -> CustomerListResponse:
    items, total = crud.list_customers(
        db,
        filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by.value,
        order=order.value,
    )
    total_pages = ceil(total / page_size) if total else 0
    return CustomerListResponse(
        data=[CustomerOut.model_validate(item) for item in items],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
    )


@router.get(
    "/stats",
    response_model=StatsResponse,
    tags=["statistics"],
    summary="Aggregate statistics over the (optionally filtered) customer set.",
)
def stats(
    filters: crud.CustomerFilters = Depends(customer_filters),
    db: Session = Depends(get_db),
) -> StatsResponse:
    return StatsResponse(**crud.get_stats(db, filters))


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    summary="Retrieve a single customer by ID.",
    responses={404: {"model": ErrorResponse, "description": "Customer not found."}},
)
def get_customer(
    customer_id: int = Path(..., ge=1, description="Customer identifier."),
    db: Session = Depends(get_db),
) -> CustomerOut:
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=404, detail=f"Customer with id {customer_id} not found."
        )
    return CustomerOut.model_validate(customer)


app.include_router(router)
