"""REST API over the Mall Customers shopping dataset."""

from __future__ import annotations

import math
import sqlite3
from typing import Annotated, Iterator

from fastapi import Depends, FastAPI, HTTPException, Query

from .database import connect, get_db_path
from .schemas import Customer, CustomerPage, Genre, GenreStats, SortField, SortOrder, Stats

app = FastAPI(
    title="Shopping API",
    description="REST API exposing the Mall Customers shopping dataset.",
    version="1.0.0",
)


def get_db() -> Iterator[sqlite3.Connection]:
    if not get_db_path().exists():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Run `python scripts/import_data.py` first.",
        )
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


DB = Annotated[sqlite3.Connection, Depends(get_db)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/customers", response_model=CustomerPage)
def list_customers(
    db: DB,
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Records per page")] = 20,
    genre: Annotated[Genre | None, Query(description="Filter by genre")] = None,
    min_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Minimum annual income (k$)")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Maximum annual income (k$)")] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    sort_by: Annotated[SortField, Query(description="Sort field")] = SortField.ID,
    order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.ASC,
) -> CustomerPage:
    for low, high, name in (
        (min_age, max_age, "age"),
        (min_income, max_income, "income"),
        (min_score, max_score, "score"),
    ):
        if low is not None and high is not None and low > high:
            raise HTTPException(
                status_code=422,
                detail=f"min_{name} ({low}) cannot be greater than max_{name} ({high})",
            )

    clauses: list[str] = []
    params: list[object] = []
    filters = [
        ("genre = ?", genre.value if genre else None),
        ("age >= ?", min_age),
        ("age <= ?", max_age),
        ("annual_income_k >= ?", min_income),
        ("annual_income_k <= ?", max_income),
        ("spending_score >= ?", min_score),
        ("spending_score <= ?", max_score),
    ]
    for clause, value in filters:
        if value is not None:
            clauses.append(clause)
            params.append(value)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    total = db.execute(f"SELECT COUNT(*) FROM customers {where}", params).fetchone()[0]

    # sort_by/order are validated enums, so interpolating them is safe.
    rows = db.execute(
        f"SELECT * FROM customers {where}"
        f" ORDER BY {sort_by.value} {order.value.upper()}, id ASC"
        " LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()

    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@app.get("/customers/search", response_model=CustomerPage)
def search_customers(
    db: DB,
    q: Annotated[str, Query(min_length=1, max_length=50, description="Search term")],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CustomerPage:
    """Basic search: matches the zero-padded customer id (e.g. "0042")
    or the genre, both as case-insensitive substrings."""
    term = f"%{q.strip().lower()}%"
    where = "WHERE printf('%04d', id) LIKE ? OR LOWER(genre) LIKE ?"
    params = [term, term]

    total = db.execute(f"SELECT COUNT(*) FROM customers {where}", params).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM customers {where} ORDER BY id LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()

    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int, db: DB) -> Customer:
    row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return Customer(**dict(row))


@app.get("/stats", response_model=Stats)
def stats(db: DB) -> Stats:
    overall = db.execute(
        "SELECT COUNT(*) AS count, AVG(age) AS avg_age,"
        " AVG(annual_income_k) AS avg_income, AVG(spending_score) AS avg_score"
        " FROM customers"
    ).fetchone()
    if not overall["count"]:
        raise HTTPException(status_code=404, detail="No customers in the database")

    by_genre: dict[str, GenreStats] = {}
    for row in db.execute(
        "SELECT genre, COUNT(*) AS count, AVG(age) AS avg_age,"
        " AVG(annual_income_k) AS avg_income, AVG(spending_score) AS avg_score"
        " FROM customers GROUP BY genre"
    ):
        by_genre[row["genre"]] = GenreStats(
            count=row["count"],
            avg_age=round(row["avg_age"], 2),
            avg_annual_income_k=round(row["avg_income"], 2),
            avg_spending_score=round(row["avg_score"], 2),
        )

    return Stats(
        total_customers=overall["count"],
        avg_age=round(overall["avg_age"], 2),
        avg_annual_income_k=round(overall["avg_income"], 2),
        avg_spending_score=round(overall["avg_score"], 2),
        by_genre=by_genre,
    )
