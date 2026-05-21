"""FastAPI entry point for the shopping dataset REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.db import get_db, init_db
from app.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerPage,
    CustomerUpdate,
    PageMeta,
    Stats,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Shopping Customers API",
    version="0.1.0",
    description="REST API over the Mall Customers shopping dataset.",
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats", response_model=Stats, tags=["meta"])
def get_stats(db: Annotated[Session, Depends(get_db)]) -> Stats:
    return Stats(**crud.stats(db))


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
def list_customers(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(50, ge=1, le=500, description="Page size, max 500."),
    offset: int = Query(0, ge=0),
    genre: str | None = Query(None, description="Filter by genre (Male/Female), case-insensitive."),
    min_age: int | None = Query(None, ge=0, le=150),
    max_age: int | None = Query(None, ge=0, le=150),
    min_income: int | None = Query(None, ge=0),
    max_income: int | None = Query(None, ge=0),
    min_score: int | None = Query(None, ge=1, le=100),
    max_score: int | None = Query(None, ge=1, le=100),
    search: str | None = Query(None, min_length=1, description="Substring search on genre and id."),
    sort_by: str = Query("customer_id", pattern="^(customer_id|age|annual_income_k|spending_score)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> CustomerPage:
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "min_age must be <= max_age")
    if min_income is not None and max_income is not None and min_income > max_income:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "min_income must be <= max_income")
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "min_score must be <= max_score")

    items, total = crud.list_customers(
        db,
        limit=limit,
        offset=offset,
        genre=genre,
        min_age=min_age,
        max_age=max_age,
        min_income=min_income,
        max_income=max_income,
        min_score=min_score,
        max_score=max_score,
        search=search,
        sort_by=sort_by,  # type: ignore[arg-type]
        sort_order=sort_order,  # type: ignore[arg-type]
    )
    return CustomerPage(
        meta=PageMeta(total=total, limit=limit, offset=offset),
        items=[CustomerOut.model_validate(c) for c in items],
    )


@app.get("/customers/{customer_id}", response_model=CustomerOut, tags=["customers"])
def get_customer(customer_id: int, db: Annotated[Session, Depends(get_db)]) -> CustomerOut:
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Customer {customer_id} not found")
    return CustomerOut.model_validate(customer)


@app.post(
    "/customers",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
    tags=["customers"],
)
def create_customer(
    payload: CustomerCreate, db: Annotated[Session, Depends(get_db)]
) -> CustomerOut:
    try:
        customer = crud.create_customer(db, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return CustomerOut.model_validate(customer)


@app.patch("/customers/{customer_id}", response_model=CustomerOut, tags=["customers"])
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerOut:
    customer = crud.update_customer(db, customer_id, payload)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Customer {customer_id} not found")
    return CustomerOut.model_validate(customer)


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["customers"])
def delete_customer(
    customer_id: int, db: Annotated[Session, Depends(get_db)]
) -> Response:
    ok = crud.delete_customer(db, customer_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Customer {customer_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
