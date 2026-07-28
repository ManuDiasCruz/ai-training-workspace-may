"""Shop API — REST endpoints over the shopping customers dataset."""

import math
import sqlite3
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query

from app.database import get_connection
from app.schemas import Customer, CustomerPage, GenreStats, Stats

app = FastAPI(
    title="Shop API",
    description="REST API over the mall shopping customers dataset "
    "(gender, age, annual income, spending score).",
    version="1.0.0",
)

SORTABLE_COLUMNS = {"customer_id", "age", "annual_income", "spending_score"}


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health", tags=["meta"])
def health(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> dict:
    try:
        count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    except sqlite3.OperationalError:
        raise HTTPException(
            status_code=503,
            detail="Database not initialised. Run scripts/import_data.py first.",
        )
    return {"status": "ok", "customers": count}


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
def list_customers(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    genre: Annotated[
        Literal["Male", "Female"] | None, Query(description="Filter by genre")
    ] = None,
    min_age: Annotated[int | None, Query(ge=0)] = None,
    max_age: Annotated[int | None, Query(ge=0)] = None,
    min_income: Annotated[int | None, Query(ge=0, description="Min annual income (k$)")] = None,
    max_income: Annotated[int | None, Query(ge=0, description="Max annual income (k$)")] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    sort_by: Annotated[
        Literal["customer_id", "age", "annual_income", "spending_score"],
        Query(description="Sort column"),
    ] = "customer_id",
    order: Annotated[Literal["asc", "desc"], Query(description="Sort direction")] = "asc",
) -> CustomerPage:
    """List customers with pagination, filtering and sorting."""
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(status_code=422, detail="min_age must be <= max_age")
    if min_income is not None and max_income is not None and min_income > max_income:
        raise HTTPException(status_code=422, detail="min_income must be <= max_income")
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(status_code=422, detail="min_score must be <= max_score")

    clauses: list[str] = []
    params: list = []
    for column, op, value in (
        ("genre", "=", genre),
        ("age", ">=", min_age),
        ("age", "<=", max_age),
        ("annual_income", ">=", min_income),
        ("annual_income", "<=", max_income),
        ("spending_score", ">=", min_score),
        ("spending_score", "<=", max_score),
    ):
        if value is not None:
            clauses.append(f"{column} {op} ?")
            params.append(value)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = conn.execute(f"SELECT COUNT(*) FROM customers{where}", params).fetchone()[0]

    rows = conn.execute(
        f"SELECT * FROM customers{where} ORDER BY {sort_by} {order.upper()}"
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


@app.get("/customers/search", response_model=CustomerPage, tags=["customers"])
def search_customers(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    q: Annotated[str, Query(min_length=1, description="Search term (matches customer id or genre)")],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CustomerPage:
    """Basic search: matches the customer id or the genre (case-insensitive)."""
    like = f"%{q.strip()}%"
    where = (
        " WHERE CAST(customer_id AS TEXT) LIKE ?"
        " OR printf('%04d', customer_id) LIKE ?"
        " OR genre LIKE ?"
    )
    params = [like, like, like]
    total = conn.execute(f"SELECT COUNT(*) FROM customers{where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM customers{where} ORDER BY customer_id LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()
    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
def get_customer(
    customer_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Customer:
    row = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return Customer(**dict(row))


@app.get("/stats", response_model=Stats, tags=["stats"])
def stats(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> Stats:
    """Aggregate statistics over the whole dataset, plus a per-genre breakdown."""
    overall = conn.execute(
        "SELECT COUNT(*) AS n, AVG(age) AS a, AVG(annual_income) AS i,"
        " AVG(spending_score) AS s FROM customers"
    ).fetchone()
    if not overall["n"]:
        raise HTTPException(status_code=404, detail="No customers in database")

    by_genre = conn.execute(
        "SELECT genre, COUNT(*) AS n, AVG(age) AS a, AVG(annual_income) AS i,"
        " AVG(spending_score) AS s FROM customers GROUP BY genre ORDER BY genre"
    ).fetchall()

    return Stats(
        total_customers=overall["n"],
        avg_age=round(overall["a"], 2),
        avg_annual_income=round(overall["i"], 2),
        avg_spending_score=round(overall["s"], 2),
        by_genre=[
            GenreStats(
                genre=row["genre"],
                count=row["n"],
                avg_age=round(row["a"], 2),
                avg_annual_income=round(row["i"], 2),
                avg_spending_score=round(row["s"], 2),
            )
            for row in by_genre
        ],
    )
