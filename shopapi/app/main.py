"""ShopAPI - REST API over the mall customers shopping dataset."""

import math
import sqlite3
from contextlib import asynccontextmanager
from enum import Enum
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app.database import get_connection, init_db
from app.schemas import Customer, CustomerPage, GenreStats, StatsSummary


class Genre(str, Enum):
    male = "Male"
    female = "Female"


class SortField(str, Enum):
    customer_id = "customer_id"
    age = "age"
    annual_income_k = "annual_income_k"
    spending_score = "spending_score"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


@asynccontextmanager
async def lifespan(_: FastAPI):
    conn = get_connection()
    try:
        init_db(conn)
    finally:
        conn.close()
    yield


app = FastAPI(
    title="ShopAPI",
    description="REST API exposing the mall customers shopping dataset.",
    version="1.0.0",
    lifespan=lifespan,
)


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


DB = Annotated[sqlite3.Connection, Depends(get_db)]


@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(_, exc: sqlite3.Error):
    return JSONResponse(status_code=500, content={"detail": f"Database error: {exc}"})


def check_range(name: str, low: int | None, high: int | None) -> None:
    if low is not None and high is not None and low > high:
        raise HTTPException(
            status_code=400,
            detail=f"min_{name} ({low}) cannot be greater than max_{name} ({high})",
        )


def paginate(
    conn: sqlite3.Connection,
    where: str,
    params: list,
    page: int,
    page_size: int,
    order_sql: str = "ORDER BY customer_id ASC",
) -> CustomerPage:
    total = conn.execute(
        f"SELECT COUNT(*) FROM customers {where}", params
    ).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM customers {where} {order_sql} LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()
    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@app.get("/health")
def health(conn: DB):
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return {"status": "ok", "customers": count}


@app.get("/customers", response_model=CustomerPage)
def list_customers(
    conn: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    genre: Genre | None = None,
    min_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0)] = None,
    max_income: Annotated[int | None, Query(ge=0)] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    sort_by: SortField = SortField.customer_id,
    order: SortOrder = SortOrder.asc,
):
    """List customers with pagination, filtering and sorting."""
    check_range("age", min_age, max_age)
    check_range("income", min_income, max_income)
    check_range("score", min_score, max_score)

    clauses, params = [], []
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
    order_sql = f"ORDER BY {sort_by.value} {order.value.upper()}, customer_id ASC"
    return paginate(conn, where, params, page, page_size, order_sql)


@app.get("/customers/search", response_model=CustomerPage)
def search_customers(
    conn: DB,
    q: Annotated[str, Query(min_length=1, max_length=50)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Search customers.

    A numeric query matches the customer ID exactly; a text query matches
    the genre (case-insensitive substring).
    """
    term = q.strip()
    if term.isdigit():
        where, params = "WHERE customer_id = ?", [int(term)]
    else:
        where, params = "WHERE genre LIKE ?", [f"%{term}%"]
    return paginate(conn, where, params, page, page_size)


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(conn: DB, customer_id: int):
    row = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return Customer(**dict(row))


@app.get("/stats/summary", response_model=StatsSummary)
def stats_summary(conn: DB):
    totals = conn.execute(
        """
        SELECT COUNT(*) AS n, AVG(age) AS avg_age,
               AVG(annual_income_k) AS avg_income, AVG(spending_score) AS avg_score,
               MIN(annual_income_k) AS min_income, MAX(annual_income_k) AS max_income
        FROM customers
        """
    ).fetchone()
    if not totals["n"]:
        raise HTTPException(status_code=404, detail="No customers in the database")

    by_genre = {
        row["genre"]: GenreStats(
            count=row["n"],
            avg_age=round(row["avg_age"], 2),
            avg_annual_income_k=round(row["avg_income"], 2),
            avg_spending_score=round(row["avg_score"], 2),
        )
        for row in conn.execute(
            """
            SELECT genre, COUNT(*) AS n, AVG(age) AS avg_age,
                   AVG(annual_income_k) AS avg_income, AVG(spending_score) AS avg_score
            FROM customers GROUP BY genre
            """
        )
    }
    return StatsSummary(
        total_customers=totals["n"],
        avg_age=round(totals["avg_age"], 2),
        avg_annual_income_k=round(totals["avg_income"], 2),
        avg_spending_score=round(totals["avg_score"], 2),
        min_annual_income_k=totals["min_income"],
        max_annual_income_k=totals["max_income"],
        by_genre=by_genre,
    )
