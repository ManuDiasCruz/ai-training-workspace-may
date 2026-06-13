from __future__ import annotations

import math
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Customer
from .schemas import CustomerOut, CustomerPage, GenreStat, PageMeta, StatsOut
from .search_index import build_match_query, ensure_search_index


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    ensure_search_index(engine)
    yield


app = FastAPI(
    title="Shopping Customer Dataset API",
    description="Read-only REST API over the Drive shopping customer dataset.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _apply_filters(
    stmt,
    *,
    genre: str | None,
    min_age: int | None,
    max_age: int | None,
    min_annual_income_k: int | None,
    max_annual_income_k: int | None,
    min_spending_score: int | None,
    max_spending_score: int | None,
):
    if genre:
        stmt = stmt.where(Customer.genre == genre)
    if min_age is not None:
        stmt = stmt.where(Customer.age >= min_age)
    if max_age is not None:
        stmt = stmt.where(Customer.age <= max_age)
    if min_annual_income_k is not None:
        stmt = stmt.where(Customer.annual_income_k >= min_annual_income_k)
    if max_annual_income_k is not None:
        stmt = stmt.where(Customer.annual_income_k <= max_annual_income_k)
    if min_spending_score is not None:
        stmt = stmt.where(Customer.spending_score >= min_spending_score)
    if max_spending_score is not None:
        stmt = stmt.where(Customer.spending_score <= max_spending_score)
    return stmt


def _validate_range(name: str, low: int | None, high: int | None) -> None:
    if low is not None and high is not None and low > high:
        raise HTTPException(status_code=400, detail=f"{name} minimum cannot exceed maximum")


def _page_response(
    db: Session,
    count_stmt,
    items_stmt,
    *,
    page: int,
    page_size: int,
) -> CustomerPage:
    total = db.scalar(count_stmt) or 0
    items = db.scalars(
        items_stmt.order_by(Customer.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    pages = math.ceil(total / page_size) if total else 0
    return CustomerPage(
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
        items=[CustomerOut.model_validate(it) for it in items],
    )


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
async def list_customers(
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    genre: str | None = Query(None, pattern=r"^(Male|Female)$"),
    min_age: int | None = Query(None, ge=0),
    max_age: int | None = Query(None, ge=0),
    min_annual_income_k: int | None = Query(None, ge=0),
    max_annual_income_k: int | None = Query(None, ge=0),
    min_spending_score: int | None = Query(None, ge=1, le=100),
    max_spending_score: int | None = Query(None, ge=1, le=100),
) -> CustomerPage:
    _validate_range("age", min_age, max_age)
    _validate_range("annual_income_k", min_annual_income_k, max_annual_income_k)
    _validate_range("spending_score", min_spending_score, max_spending_score)

    filters = dict(
        genre=genre,
        min_age=min_age,
        max_age=max_age,
        min_annual_income_k=min_annual_income_k,
        max_annual_income_k=max_annual_income_k,
        min_spending_score=min_spending_score,
        max_spending_score=max_spending_score,
    )
    return _page_response(
        db,
        _apply_filters(select(func.count(Customer.id)), **filters),
        _apply_filters(select(Customer), **filters),
        page=page,
        page_size=page_size,
    )


@app.get("/customers/{customer_id}", response_model=CustomerOut, tags=["customers"])
async def get_customer(customer_id: str, db: Annotated[Session, Depends(get_db)]) -> CustomerOut:
    obj = db.scalar(select(Customer).where(Customer.customer_id == customer_id))
    if obj is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerOut.model_validate(obj)


@app.get("/search", response_model=CustomerPage, tags=["customers"])
async def search_customers(
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(..., min_length=1, max_length=64, description="Free-text search"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> CustomerPage:
    match_query = build_match_query(q)
    if match_query is None:
        return CustomerPage(
            meta=PageMeta(total=0, page=page, page_size=page_size, pages=0),
            items=[],
        )

    params = {
        "match_query": match_query,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    total = int(
        db.scalar(
            text(
                "SELECT count(*) FROM customers_fts "
                "WHERE customers_fts MATCH :match_query"
            ),
            params,
        )
        or 0
    )
    rows = db.execute(
        text(
            """
            SELECT
                customers.id,
                customers.customer_id,
                customers.genre,
                customers.age,
                customers.annual_income_k,
                customers.spending_score
            FROM customers_fts
            JOIN customers ON customers.id = customers_fts.rowid
            WHERE customers_fts MATCH :match_query
            ORDER BY bm25(customers_fts, 8.0, 4.0, 1.0, 1.0, 1.0), customers.id
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings()
    return CustomerPage(
        meta=PageMeta(
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        ),
        items=[CustomerOut.model_validate(row) for row in rows],
    )


@app.get("/genres", response_model=list[str], tags=["meta"])
async def list_genres(db: Annotated[Session, Depends(get_db)]) -> list[str]:
    rows = db.scalars(select(Customer.genre).distinct().order_by(Customer.genre)).all()
    return list(rows)


@app.get("/stats", response_model=StatsOut, tags=["meta"])
async def stats(db: Annotated[Session, Depends(get_db)]) -> StatsOut:
    total = db.scalar(select(func.count(Customer.id))) or 0
    if total == 0:
        return StatsOut(
            total_customers=0,
            avg_age=0.0,
            avg_annual_income_k=0.0,
            avg_spending_score=0.0,
            by_genre=[],
        )

    genre_rows = db.execute(
        select(
            Customer.genre,
            func.count(Customer.id),
            func.avg(Customer.age),
            func.avg(Customer.annual_income_k),
            func.avg(Customer.spending_score),
        )
        .group_by(Customer.genre)
        .order_by(Customer.genre)
    ).all()
    by_genre = [
        GenreStat(
            genre=r[0],
            count=int(r[1]),
            avg_age=round(float(r[2] or 0), 2),
            avg_annual_income_k=round(float(r[3] or 0), 2),
            avg_spending_score=round(float(r[4] or 0), 2),
        )
        for r in genre_rows
    ]
    return StatsOut(
        total_customers=total,
        avg_age=round(float(db.scalar(select(func.avg(Customer.age))) or 0), 2),
        avg_annual_income_k=round(float(db.scalar(select(func.avg(Customer.annual_income_k))) or 0), 2),
        avg_spending_score=round(float(db.scalar(select(func.avg(Customer.spending_score))) or 0), 2),
        min_age=db.scalar(select(func.min(Customer.age))),
        max_age=db.scalar(select(func.max(Customer.age))),
        min_annual_income_k=db.scalar(select(func.min(Customer.annual_income_k))),
        max_annual_income_k=db.scalar(select(func.max(Customer.annual_income_k))),
        min_spending_score=db.scalar(select(func.min(Customer.spending_score))),
        max_spending_score=db.scalar(select(func.max(Customer.spending_score))),
        by_genre=by_genre,
    )
