from __future__ import annotations

import math
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import String, cast, func, or_, select, text
from sqlalchemy.orm import Session

from . import search_index
from .db import Base, engine, get_db
from .models import Customer
from .schemas import CustomerOut, CustomerPage, GenreStat, PageMeta, StatsOut


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        search_index.rebuild_search_index(conn)
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


def _legacy_search(
    db: Session, q: str, page: int, page_size: int
) -> CustomerPage:
    """ILIKE substring search, used when FTS5 is unavailable in this SQLite build."""
    like = f"%{q}%"
    cond = or_(
        Customer.customer_id.ilike(like),
        Customer.genre.ilike(like),
        cast(Customer.age, String).ilike(like),
        cast(Customer.annual_income_k, String).ilike(like),
        cast(Customer.spending_score, String).ilike(like),
    )
    return _page_response(
        db,
        select(func.count(Customer.id)).where(cond),
        select(Customer).where(cond),
        page=page,
        page_size=page_size,
    )


_SEARCH_CAPS: dict[str, bool] | None = None


def _search_caps(db: Session) -> dict[str, bool]:
    global _SEARCH_CAPS
    if _SEARCH_CAPS is None:
        _SEARCH_CAPS = search_index.detect_capabilities(db.connection())
    return _SEARCH_CAPS


@app.get("/search", response_model=CustomerPage, tags=["customers"])
async def search_customers(
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(..., min_length=1, max_length=64, description="Free-text search"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    fuzzy: bool = Query(
        False, description="Trigram-based substring / typo-tolerant matching"
    ),
) -> CustomerPage:
    """Full-text search over customers, ranked by BM25 relevance (FTS5).

    Falls back to a simple ILIKE search if the running SQLite build has no
    FTS5 support. ``fuzzy=true`` switches to the trigram index for
    substring/typo tolerance when available.
    """
    caps = _search_caps(db)
    if not caps["fts5"]:
        return _legacy_search(db, q, page, page_size)

    use_trgm = fuzzy and caps["trigram"]
    match = search_index.build_match_query(q, fuzzy=use_trgm)
    if match is None and use_trgm:
        # Fuzzy query too short for trigram tokens; fall back to prefix match.
        use_trgm = False
        match = search_index.build_match_query(q, fuzzy=False)
    if match is None:
        return CustomerPage(
            meta=PageMeta(total=0, page=page, page_size=page_size, pages=0), items=[]
        )

    table = search_index.FTS_TRGM_TABLE if use_trgm else search_index.FTS_TABLE
    total = (
        db.execute(
            text(f"SELECT count(*) FROM {table} WHERE {table} MATCH :m"), {"m": match}
        ).scalar()
        or 0
    )
    rows = (
        db.execute(
            text(
                f"SELECT c.id, c.customer_id, c.genre, c.age, c.annual_income_k, "
                f"c.spending_score FROM {table} JOIN customers c ON c.id = {table}.rowid "
                f"WHERE {table} MATCH :m ORDER BY bm25({table}), c.id "
                f"LIMIT :limit OFFSET :offset"
            ),
            {"m": match, "limit": page_size, "offset": (page - 1) * page_size},
        )
        .mappings()
        .all()
    )
    pages = math.ceil(total / page_size) if total else 0
    return CustomerPage(
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
        items=[CustomerOut.model_validate(dict(r)) for r in rows],
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
