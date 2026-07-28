"""FastAPI application exposing the shopping customers dataset."""

import math
import sqlite3
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi import Path as PathParam

from app.database import db_is_ready, get_connection
from app.models import Customer, CustomerPage, GenreStats, Stats

app = FastAPI(
    title="Shop API",
    description=(
        "REST API over the mall-customers shopping dataset "
        "(200 customers: genre, age, annual income, spending score)."
    ),
    version="1.0.0",
)

SORTABLE_COLUMNS = {
    "id": "id",
    "genre": "genre",
    "age": "age",
    "annual_income_k": "annual_income_k",
    "spending_score": "spending_score",
}


def get_db() -> sqlite3.Connection:
    if not db_is_ready():
        raise HTTPException(
            status_code=503,
            detail="Database not initialised. Run 'python scripts/import_data.py' first.",
        )
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


DbDep = Annotated[sqlite3.Connection, Depends(get_db)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/customers", response_model=CustomerPage)
def list_customers(
    db: DbDep,
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    genre: Annotated[
        Literal["Male", "Female", "male", "female"] | None,
        Query(description="Filter by genre"),
    ] = None,
    min_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    max_age: Annotated[int | None, Query(ge=1, le=120)] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Min annual income (k$)")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Max annual income (k$)")] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=50, description="Search by customer id or genre substring"),
    ] = None,
    sort_by: Annotated[
        Literal["id", "genre", "age", "annual_income_k", "spending_score"],
        Query(description="Column to sort by"),
    ] = "id",
    sort_dir: Annotated[Literal["asc", "desc"], Query(description="Sort direction")] = "asc",
) -> CustomerPage:
    """List customers with pagination, filtering, search and sorting."""
    for name, low, high in (
        ("age", min_age, max_age),
        ("income", min_income, max_income),
        ("score", min_score, max_score),
    ):
        if low is not None and high is not None and low > high:
            raise HTTPException(
                status_code=400,
                detail=f"min_{name} ({low}) cannot be greater than max_{name} ({high})",
            )

    where: list[str] = []
    params: list[object] = []

    if genre is not None:
        where.append("genre = ?")
        params.append(genre.title())
    for clause, value in (
        ("age >= ?", min_age),
        ("age <= ?", max_age),
        ("annual_income_k >= ?", min_income),
        ("annual_income_k <= ?", max_income),
        ("spending_score >= ?", min_score),
        ("spending_score <= ?", max_score),
    ):
        if value is not None:
            where.append(clause)
            params.append(value)
    if q is not None:
        term = q.strip()
        if term.isdigit():
            where.append("id = ?")
            params.append(int(term))
        else:
            where.append("LOWER(genre) LIKE ?")
            params.append(f"%{term.lower()}%")

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    order_sql = f"ORDER BY {SORTABLE_COLUMNS[sort_by]} {sort_dir.upper()}, id ASC"

    total_items = db.execute(
        f"SELECT COUNT(*) FROM customers {where_sql}", params
    ).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM customers {where_sql} {order_sql} LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()

    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=max(1, math.ceil(total_items / page_size)),
    )


@app.get("/customers/stats", response_model=Stats)
def customer_stats(db: DbDep) -> Stats:
    """Aggregate statistics over the whole dataset, with a per-genre breakdown."""
    overall = db.execute(
        """
        SELECT COUNT(*)                   AS total_customers,
               AVG(age)                   AS avg_age,
               AVG(annual_income_k)       AS avg_annual_income_k,
               AVG(spending_score)        AS avg_spending_score,
               MIN(annual_income_k)       AS min_annual_income_k,
               MAX(annual_income_k)       AS max_annual_income_k
        FROM customers
        """
    ).fetchone()
    if overall["total_customers"] == 0:
        raise HTTPException(status_code=404, detail="No customers in the database")

    by_genre = db.execute(
        """
        SELECT genre,
               COUNT(*)             AS count,
               AVG(age)             AS avg_age,
               AVG(annual_income_k) AS avg_annual_income_k,
               AVG(spending_score)  AS avg_spending_score
        FROM customers
        GROUP BY genre
        ORDER BY genre
        """
    ).fetchall()

    return Stats(
        total_customers=overall["total_customers"],
        avg_age=round(overall["avg_age"], 2),
        avg_annual_income_k=round(overall["avg_annual_income_k"], 2),
        avg_spending_score=round(overall["avg_spending_score"], 2),
        min_annual_income_k=overall["min_annual_income_k"],
        max_annual_income_k=overall["max_annual_income_k"],
        by_genre=[
            GenreStats(
                genre=row["genre"],
                count=row["count"],
                avg_age=round(row["avg_age"], 2),
                avg_annual_income_k=round(row["avg_annual_income_k"], 2),
                avg_spending_score=round(row["avg_spending_score"], 2),
            )
            for row in by_genre
        ],
    )


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: Annotated[int, PathParam(ge=1)], db: DbDep) -> Customer:
    """Fetch a single customer by id."""
    row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return Customer(**dict(row))
