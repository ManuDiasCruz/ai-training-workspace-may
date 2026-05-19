from __future__ import annotations

import math
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Purchase
from .schemas import CategoryStat, PageMeta, PurchaseOut, PurchasePage, StatsOut


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Shopping Dataset API",
    description="Read-only REST API over the Customer Shopping Trends dataset.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


def _apply_filters(
    stmt,
    *,
    category: str | None,
    gender: str | None,
    location: str | None,
    season: str | None,
    min_amount: float | None,
    max_amount: float | None,
    min_rating: float | None,
):
    if category:
        stmt = stmt.where(Purchase.category == category)
    if gender:
        stmt = stmt.where(Purchase.gender == gender)
    if location:
        stmt = stmt.where(Purchase.location == location)
    if season:
        stmt = stmt.where(Purchase.season == season)
    if min_amount is not None:
        stmt = stmt.where(Purchase.purchase_amount_usd >= min_amount)
    if max_amount is not None:
        stmt = stmt.where(Purchase.purchase_amount_usd <= max_amount)
    if min_rating is not None:
        stmt = stmt.where(Purchase.review_rating >= min_rating)
    return stmt


@app.get("/purchases", response_model=PurchasePage, tags=["purchases"])
def list_purchases(
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    category: str | None = Query(None),
    gender: str | None = Query(None, pattern=r"^[A-Za-z ]+$"),
    location: str | None = Query(None),
    season: str | None = Query(None),
    min_amount: float | None = Query(None, ge=0),
    max_amount: float | None = Query(None, ge=0),
    min_rating: float | None = Query(None, ge=0, le=5),
) -> PurchasePage:
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(status_code=400, detail="min_amount cannot exceed max_amount")

    filters = dict(
        category=category, gender=gender, location=location, season=season,
        min_amount=min_amount, max_amount=max_amount, min_rating=min_rating,
    )

    total = db.scalar(_apply_filters(select(func.count(Purchase.id)), **filters)) or 0
    stmt = (
        _apply_filters(select(Purchase), **filters)
        .order_by(Purchase.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.scalars(stmt).all()
    pages = math.ceil(total / page_size) if total else 0
    return PurchasePage(
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
        items=[PurchaseOut.model_validate(it) for it in items],
    )


@app.get("/purchases/{purchase_id}", response_model=PurchaseOut, tags=["purchases"])
def get_purchase(purchase_id: int, db: Annotated[Session, Depends(get_db)]) -> PurchaseOut:
    obj = db.get(Purchase, purchase_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return PurchaseOut.model_validate(obj)


@app.get("/search", response_model=PurchasePage, tags=["purchases"])
def search_purchases(
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(..., min_length=1, max_length=128, description="Free-text search"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> PurchasePage:
    like = f"%{q}%"
    cond = or_(
        Purchase.item_purchased.ilike(like),
        Purchase.category.ilike(like),
        Purchase.color.ilike(like),
        Purchase.location.ilike(like),
    )
    total = db.scalar(select(func.count(Purchase.id)).where(cond)) or 0
    stmt = (
        select(Purchase).where(cond).order_by(Purchase.id)
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = db.scalars(stmt).all()
    pages = math.ceil(total / page_size) if total else 0
    return PurchasePage(
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
        items=[PurchaseOut.model_validate(it) for it in items],
    )


@app.get("/categories", response_model=list[str], tags=["meta"])
def list_categories(db: Annotated[Session, Depends(get_db)]) -> list[str]:
    rows = db.scalars(select(Purchase.category).distinct().order_by(Purchase.category)).all()
    return list(rows)


@app.get("/stats", response_model=StatsOut, tags=["meta"])
def stats(db: Annotated[Session, Depends(get_db)]) -> StatsOut:
    total = db.scalar(select(func.count(Purchase.id))) or 0
    if total == 0:
        return StatsOut(
            total_purchases=0, total_revenue_usd=0.0,
            avg_purchase_amount_usd=0.0, avg_review_rating=0.0, by_category=[],
        )
    total_revenue = float(db.scalar(select(func.sum(Purchase.purchase_amount_usd))) or 0.0)
    avg_amount = float(db.scalar(select(func.avg(Purchase.purchase_amount_usd))) or 0.0)
    avg_rating = float(db.scalar(select(func.avg(Purchase.review_rating))) or 0.0)

    cat_rows = db.execute(
        select(
            Purchase.category,
            func.count(Purchase.id),
            func.sum(Purchase.purchase_amount_usd),
            func.avg(Purchase.purchase_amount_usd),
            func.avg(Purchase.review_rating),
        ).group_by(Purchase.category).order_by(Purchase.category)
    ).all()
    by_category = [
        CategoryStat(
            category=r[0], count=int(r[1]),
            total_amount=round(float(r[2] or 0), 2),
            avg_amount=round(float(r[3] or 0), 2),
            avg_rating=round(float(r[4] or 0), 2),
        )
        for r in cat_rows
    ]
    return StatsOut(
        total_purchases=total,
        total_revenue_usd=round(total_revenue, 2),
        avg_purchase_amount_usd=round(avg_amount, 2),
        avg_review_rating=round(avg_rating, 2),
        by_category=by_category,
    )
