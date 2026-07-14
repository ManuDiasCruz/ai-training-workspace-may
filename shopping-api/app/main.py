"""FastAPI application exposing the shopping customers dataset."""

import sqlite3
from typing import Annotated, Iterator, Literal

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from .database import get_connection
from .schemas import Customer, CustomerPage, GenreBreakdown, StatsSummary

app = FastAPI(
    title="Shopping Customers API",
    description=(
        "REST API over the mall shopping dataset (200 customers with genre, "
        "age, annual income and spending score). Interactive docs at /docs."
    ),
    version="1.0.0",
)

VALID_GENRES = {"Male", "Female"}

SortField = Literal["customer_id", "genre", "age", "annual_income_k", "spending_score"]
SortOrder = Literal["asc", "desc"]


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


DbDep = Annotated[sqlite3.Connection, Depends(get_db)]


@app.exception_handler(sqlite3.OperationalError)
async def sqlite_operational_error_handler(request: Request, exc: sqlite3.OperationalError):
    """Missing table/database file → actionable 503 instead of a raw 500."""
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Database is not initialised or unavailable. "
                "Run 'python -m app.import_data' from the shopping-api directory, then retry."
            )
        },
    )


def _normalise_genre(genre: str | None) -> str | None:
    if genre is None:
        return None
    value = genre.strip().title()
    if value not in VALID_GENRES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid genre {genre!r}. Expected one of: Male, Female.",
        )
    return value


def _check_range(name: str, low: int | None, high: int | None) -> None:
    if low is not None and high is not None and low > high:
        raise HTTPException(
            status_code=422,
            detail=f"min_{name} ({low}) cannot be greater than max_{name} ({high}).",
        )


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _paginate(
    db: sqlite3.Connection,
    where_sql: str,
    params: list,
    page: int,
    page_size: int,
    order_sql: str = "customer_id ASC",
) -> CustomerPage:
    total = db.execute(f"SELECT COUNT(*) FROM customers{where_sql}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"SELECT * FROM customers{where_sql} ORDER BY {order_sql} LIMIT ? OFFSET ?",
        [*params, page_size, offset],
    ).fetchall()
    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=(total + page_size - 1) // page_size,
    )


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Shopping Customers API",
        "docs": "/docs",
        "endpoints": ["/health", "/customers", "/customers/search", "/customers/{id}", "/stats"],
    }


@app.get("/health", tags=["meta"])
def health(db: DbDep):
    count = db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return {"status": "ok", "customers": count}


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
def list_customers(
    db: DbDep,
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(20, ge=1, le=100, description="items per page (max 100)"),
    genre: str | None = Query(None, description="filter by genre: Male or Female (case-insensitive)"),
    min_age: int | None = Query(None, ge=1, le=120),
    max_age: int | None = Query(None, ge=1, le=120),
    min_income: int | None = Query(None, ge=0, description="minimum annual income (k$)"),
    max_income: int | None = Query(None, ge=0, description="maximum annual income (k$)"),
    min_score: int | None = Query(None, ge=1, le=100),
    max_score: int | None = Query(None, ge=1, le=100),
    sort_by: SortField = Query("customer_id"),
    order: SortOrder = Query("asc"),
):
    """List customers with pagination, field filters and sorting."""
    genre_value = _normalise_genre(genre)
    _check_range("age", min_age, max_age)
    _check_range("income", min_income, max_income)
    _check_range("score", min_score, max_score)

    clauses: list[str] = []
    params: list = []
    for condition, value in [
        ("genre = ?", genre_value),
        ("age >= ?", min_age),
        ("age <= ?", max_age),
        ("annual_income_k >= ?", min_income),
        ("annual_income_k <= ?", max_income),
        ("spending_score >= ?", min_score),
        ("spending_score <= ?", max_score),
    ]:
        if value is not None:
            clauses.append(condition)
            params.append(value)

    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    # sort_by/order come from Literal-validated enums, safe to interpolate.
    order_sql = f"{sort_by} {order.upper()}, customer_id ASC"
    return _paginate(db, where_sql, params, page, page_size, order_sql)


@app.get("/customers/search", response_model=CustomerPage, tags=["customers"])
def search_customers(
    db: DbDep,
    q: str = Query(..., min_length=1, max_length=50, description="search term (text or number)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Basic search: partial genre match, plus exact match on any numeric field.

    A numeric term matches customer_id, age, annual income or spending score;
    any term is also matched against genre (case-insensitive substring).
    """
    term = q.strip()
    if not term:
        raise HTTPException(status_code=422, detail="Search query cannot be blank.")

    clauses = [r"genre LIKE ? ESCAPE '\'"]
    params: list = [f"%{_escape_like(term)}%"]
    if term.isdigit():
        number = int(term)
        clauses += ["customer_id = ?", "age = ?", "annual_income_k = ?", "spending_score = ?"]
        params += [number, number, number, number]

    where_sql = f" WHERE {' OR '.join(clauses)}"
    return _paginate(db, where_sql, params, page, page_size)


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
def get_customer(db: DbDep, customer_id: int = Path(..., ge=1)):
    """Fetch a single customer by ID; 404 when it does not exist."""
    row = db.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")
    return Customer(**dict(row))


@app.get("/stats", response_model=StatsSummary, tags=["stats"])
def get_stats(db: DbDep):
    """Aggregate statistics over the whole dataset, with a per-genre breakdown."""
    overall = db.execute(
        "SELECT COUNT(*) AS n, AVG(age) AS avg_age,"
        " AVG(annual_income_k) AS avg_income, AVG(spending_score) AS avg_score,"
        " MIN(annual_income_k) AS min_income, MAX(annual_income_k) AS max_income"
        " FROM customers"
    ).fetchone()

    if overall["n"] == 0:
        return StatsSummary(
            total_customers=0,
            avg_age=0.0,
            avg_annual_income_k=0.0,
            avg_spending_score=0.0,
            min_annual_income_k=0,
            max_annual_income_k=0,
            by_genre=[],
        )

    genre_rows = db.execute(
        "SELECT genre, COUNT(*) AS n, AVG(age) AS avg_age,"
        " AVG(annual_income_k) AS avg_income, AVG(spending_score) AS avg_score"
        " FROM customers GROUP BY genre ORDER BY genre"
    ).fetchall()

    return StatsSummary(
        total_customers=overall["n"],
        avg_age=round(overall["avg_age"], 2),
        avg_annual_income_k=round(overall["avg_income"], 2),
        avg_spending_score=round(overall["avg_score"], 2),
        min_annual_income_k=overall["min_income"],
        max_annual_income_k=overall["max_income"],
        by_genre=[
            GenreBreakdown(
                genre=row["genre"],
                customers=row["n"],
                avg_age=round(row["avg_age"], 2),
                avg_annual_income_k=round(row["avg_income"], 2),
                avg_spending_score=round(row["avg_score"], 2),
            )
            for row in genre_rows
        ],
    )
