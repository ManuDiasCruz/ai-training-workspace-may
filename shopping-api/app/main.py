"""Shopping API — REST endpoints over the mall customers dataset."""

from contextlib import asynccontextmanager
from enum import Enum
from math import ceil
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from . import models
from .database import Base, engine, get_session
from .schemas import CustomerOut, GenreStats, PaginatedCustomers, StatsOut


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Shopping API",
    description=(
        "REST API over the mall customers shopping dataset "
        "(200 customers: genre, age, annual income, spending score)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


class Genre(str, Enum):
    male = "Male"
    female = "Female"


class SortField(str, Enum):
    id = "id"
    age = "age"
    annual_income_k = "annual_income_k"
    spending_score = "spending_score"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


SessionDep = Annotated[Session, Depends(get_session)]


def _check_range(name: str, lo: int | None, hi: int | None) -> None:
    if lo is not None and hi is not None and lo > hi:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range for {name}: min ({lo}) is greater than max ({hi}).",
        )


@app.get("/health", tags=["meta"])
def health(session: SessionDep) -> dict:
    total = session.scalar(select(func.count(models.Customer.id))) or 0
    return {"status": "ok", "customers": total}


@app.get("/customers", response_model=PaginatedCustomers, tags=["customers"])
def list_customers(
    session: SessionDep,
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    genre: Annotated[Genre | None, Query(description="Filter by genre")] = None,
    min_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Annual income (k$)")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Annual income (k$)")] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    sort_by: Annotated[SortField, Query()] = SortField.id,
    order: Annotated[SortOrder, Query()] = SortOrder.asc,
) -> PaginatedCustomers:
    """List customers with pagination, filtering and sorting."""
    _check_range("age", min_age, max_age)
    _check_range("income", min_income, max_income)
    _check_range("score", min_score, max_score)

    query = select(models.Customer)
    if genre is not None:
        query = query.where(models.Customer.genre == genre.value)
    if min_age is not None:
        query = query.where(models.Customer.age >= min_age)
    if max_age is not None:
        query = query.where(models.Customer.age <= max_age)
    if min_income is not None:
        query = query.where(models.Customer.annual_income_k >= min_income)
    if max_income is not None:
        query = query.where(models.Customer.annual_income_k <= max_income)
    if min_score is not None:
        query = query.where(models.Customer.spending_score >= min_score)
    if max_score is not None:
        query = query.where(models.Customer.spending_score <= max_score)

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0

    direction = asc if order is SortOrder.asc else desc
    sort_column = getattr(models.Customer, sort_by.value)
    query = (
        query.order_by(direction(sort_column), models.Customer.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = session.scalars(query).all()

    return PaginatedCustomers(
        items=[CustomerOut.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@app.get("/customers/search", response_model=PaginatedCustomers, tags=["customers"])
def search_customers(
    session: SessionDep,
    q: Annotated[str, Query(min_length=1, max_length=50, description="Search term")],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedCustomers:
    """Basic search.

    Matches the term (case-insensitively) against the genre, or — when the
    term is numeric — against the customer id, age, annual income or
    spending score.
    """
    term = q.strip()
    if not term:
        raise HTTPException(status_code=400, detail="Search term must not be blank.")

    conditions = [models.Customer.genre.ilike(f"%{term}%")]
    if term.isdigit():
        value = int(term)
        conditions += [
            models.Customer.id == value,
            models.Customer.age == value,
            models.Customer.annual_income_k == value,
            models.Customer.spending_score == value,
        ]

    query = select(models.Customer).where(or_(*conditions))
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = session.scalars(
        query.order_by(models.Customer.id).offset((page - 1) * page_size).limit(page_size)
    ).all()

    return PaginatedCustomers(
        items=[CustomerOut.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@app.get("/customers/{customer_id}", response_model=CustomerOut, tags=["customers"])
def get_customer(
    session: SessionDep,
    customer_id: Annotated[int, Path(ge=1)],
) -> CustomerOut:
    customer = session.get(models.Customer, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=404, detail=f"Customer {customer_id} not found."
        )
    return CustomerOut.model_validate(customer)


@app.get("/stats", response_model=StatsOut, tags=["stats"])
def stats(session: SessionDep) -> StatsOut:
    """Aggregate statistics for the whole dataset and per genre."""
    overall = session.execute(
        select(
            func.count(models.Customer.id),
            func.avg(models.Customer.age),
            func.avg(models.Customer.annual_income_k),
            func.avg(models.Customer.spending_score),
        )
    ).one()
    if not overall[0]:
        raise HTTPException(
            status_code=404,
            detail="No data imported yet. Run scripts/import_data.py first.",
        )

    by_genre: dict[str, GenreStats] = {}
    rows = session.execute(
        select(
            models.Customer.genre,
            func.count(models.Customer.id),
            func.avg(models.Customer.age),
            func.avg(models.Customer.annual_income_k),
            func.avg(models.Customer.spending_score),
        ).group_by(models.Customer.genre)
    ).all()
    for genre, count, avg_age, avg_income, avg_score in rows:
        by_genre[genre] = GenreStats(
            count=count,
            avg_age=round(avg_age, 2),
            avg_annual_income_k=round(avg_income, 2),
            avg_spending_score=round(avg_score, 2),
        )

    return StatsOut(
        total_customers=overall[0],
        avg_age=round(overall[1], 2),
        avg_annual_income_k=round(overall[2], 2),
        avg_spending_score=round(overall[3], 2),
        by_genre=by_genre,
    )
