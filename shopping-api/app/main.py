"""FastAPI application exposing the shopping dataset.

Endpoints:
    GET /health                 -> liveness probe
    GET /customers              -> list with pagination, filtering & search
    GET /customers/stats        -> aggregate statistics (respects filters)
    GET /customers/{id}         -> fetch a single customer
"""
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db

# Ensure tables exist on startup (no-op if the import script already ran).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Shopping Dataset API",
    version="1.0.0",
    description=(
        "A small REST API over the mall shopping dataset "
        "(CustomerID, Genre, Age, Annual Income, Spending Score)."
    ),
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # pragma: no cover - safety net
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/customers", response_model=schemas.PaginatedCustomers, tags=["customers"])
def list_customers(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    sort_by: str = Query("customer_id", pattern="^(customer_id|age|annual_income|spending_score)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    genre: Optional[str] = Query(None, pattern="^(Male|Female)$"),
    min_age: Optional[int] = Query(None, ge=0, le=120),
    max_age: Optional[int] = Query(None, ge=0, le=120),
    min_income: Optional[int] = Query(None, ge=0),
    max_income: Optional[int] = Query(None, ge=0),
    min_spending_score: Optional[int] = Query(None, ge=1, le=100),
    max_spending_score: Optional[int] = Query(None, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=64, description="Free-text search"),
):
    """List customers with pagination, range filtering and free-text search."""
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(status_code=422, detail="min_age cannot exceed max_age")
    if min_income is not None and max_income is not None and min_income > max_income:
        raise HTTPException(status_code=422, detail="min_income cannot exceed max_income")
    if (
        min_spending_score is not None
        and max_spending_score is not None
        and min_spending_score > max_spending_score
    ):
        raise HTTPException(
            status_code=422, detail="min_spending_score cannot exceed max_spending_score"
        )

    total, items = crud.list_customers(
        db,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        genre=genre,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_spending_score=min_spending_score,
        max_spending_score=max_spending_score,
        search=search,
    )
    return schemas.PaginatedCustomers(
        total=total, limit=limit, offset=offset, count=len(items), items=items
    )


@app.get("/customers/stats", response_model=schemas.StatsSummary, tags=["customers"])
def customer_stats(
    db: Session = Depends(get_db),
    genre: Optional[str] = Query(None, pattern="^(Male|Female)$"),
    min_age: Optional[int] = Query(None, ge=0, le=120),
    max_age: Optional[int] = Query(None, ge=0, le=120),
    min_income: Optional[int] = Query(None, ge=0),
    max_income: Optional[int] = Query(None, ge=0),
):
    """Aggregate statistics over the dataset, honouring the same filters."""
    return crud.stats(
        db,
        genre=genre,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
    )


@app.get(
    "/customers/{customer_id}",
    response_model=schemas.Customer,
    responses={404: {"model": schemas.ErrorResponse}},
    tags=["customers"],
)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Fetch a single customer by id (e.g. ``0042``)."""
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    return customer
