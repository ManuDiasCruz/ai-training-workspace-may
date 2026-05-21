from __future__ import annotations

import math
import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from .database import connect, customer_count
from .schemas import CustomerListResponse, CustomerOut, PaginationMeta, SummaryResponse


app = FastAPI(
    title="Shopping Dataset API",
    description="Read-only API over the shopping customer CSV imported into local SQLite.",
    version="1.0.0",
)


def _normalize_genre_filter(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().capitalize()
    if normalized not in {"Male", "Female"}:
        raise HTTPException(status_code=400, detail="genre must be Male or Female")
    return normalized


def _normalize_customer_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized.isdigit() and len(normalized) < 4:
        normalized = normalized.zfill(4)
    return normalized


def _validate_min_max(min_value: int | None, max_value: int | None, label: str) -> None:
    if min_value is not None and max_value is not None and min_value > max_value:
        raise HTTPException(
            status_code=400,
            detail=f"min_{label} cannot be greater than max_{label}",
        )


def _build_list_response(
    connection: sqlite3.Connection,
    where_sql: str,
    values: list[Any],
    page: int,
    page_size: int,
) -> CustomerListResponse:
    total_row = connection.execute(
        f"SELECT COUNT(*) AS total FROM customers {where_sql}",
        values,
    ).fetchone()
    total = int(total_row["total"])
    pages = math.ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size

    rows = connection.execute(
        f"""
        SELECT customer_id, genre, age, annual_income_k, spending_score
        FROM customers
        {where_sql}
        ORDER BY customer_id
        LIMIT ? OFFSET ?
        """,
        [*values, page_size, offset],
    ).fetchall()
    return CustomerListResponse(
        meta=PaginationMeta(total=total, page=page, page_size=page_size, pages=pages),
        items=[CustomerOut(**dict(row)) for row in rows],
    )


@app.get("/health")
async def health() -> dict[str, int | str]:
    return {"status": "ok", "customers": customer_count()}


@app.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    genre: str | None = Query(default=None),
    customer_id: str | None = Query(default=None),
    min_age: int | None = Query(default=None, ge=0, le=120),
    max_age: int | None = Query(default=None, ge=0, le=120),
    min_income: int | None = Query(default=None, ge=0),
    max_income: int | None = Query(default=None, ge=0),
    min_spending_score: int | None = Query(default=None, ge=0, le=100),
    max_spending_score: int | None = Query(default=None, ge=0, le=100),
) -> CustomerListResponse:
    _validate_min_max(min_age, max_age, "age")
    _validate_min_max(min_income, max_income, "income")
    _validate_min_max(min_spending_score, max_spending_score, "spending_score")

    conditions: list[str] = []
    values: list[Any] = []

    normalized_genre = _normalize_genre_filter(genre)
    if normalized_genre is not None:
        conditions.append("genre = ?")
        values.append(normalized_genre)

    normalized_customer_id = _normalize_customer_id(customer_id)
    if normalized_customer_id:
        conditions.append("customer_id = ?")
        values.append(normalized_customer_id)

    for field, min_value, max_value in [
        ("age", min_age, max_age),
        ("annual_income_k", min_income, max_income),
        ("spending_score", min_spending_score, max_spending_score),
    ]:
        if min_value is not None:
            conditions.append(f"{field} >= ?")
            values.append(min_value)
        if max_value is not None:
            conditions.append(f"{field} <= ?")
            values.append(max_value)

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with connect() as connection:
        return _build_list_response(connection, where_sql, values, page, page_size)


@app.get("/customers/{customer_id}", response_model=CustomerOut)
async def get_customer(customer_id: str) -> CustomerOut:
    normalized_customer_id = _normalize_customer_id(customer_id)
    with connect() as connection:
        row = connection.execute(
            """
            SELECT customer_id, genre, age, annual_income_k, spending_score
            FROM customers
            WHERE customer_id = ?
            """,
            [normalized_customer_id],
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return CustomerOut(**dict(row))


@app.get("/search", response_model=CustomerListResponse)
async def search_customers(
    q: str = Query(min_length=1, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CustomerListResponse:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=422, detail="q must not be blank")

    like_value = f"%{query}%"
    where_sql = """
        WHERE customer_id LIKE ?
        OR LOWER(genre) LIKE LOWER(?)
        OR CAST(age AS TEXT) LIKE ?
        OR CAST(annual_income_k AS TEXT) LIKE ?
        OR CAST(spending_score AS TEXT) LIKE ?
    """
    values = [like_value, like_value, like_value, like_value, like_value]
    with connect() as connection:
        return _build_list_response(connection, where_sql, values, page, page_size)


@app.get("/summary", response_model=SummaryResponse)
async def get_summary() -> SummaryResponse:
    with connect() as connection:
        overall = connection.execute(
            """
            SELECT
                COUNT(*) AS total_customers,
                COALESCE(AVG(age), 0) AS average_age,
                COALESCE(AVG(annual_income_k), 0) AS average_annual_income_k,
                COALESCE(AVG(spending_score), 0) AS average_spending_score
            FROM customers
            """
        ).fetchone()
        by_genre_rows = connection.execute(
            """
            SELECT
                genre,
                COUNT(*) AS count,
                COALESCE(AVG(age), 0) AS average_age,
                COALESCE(AVG(annual_income_k), 0) AS average_annual_income_k,
                COALESCE(AVG(spending_score), 0) AS average_spending_score
            FROM customers
            GROUP BY genre
            ORDER BY genre
            """
        ).fetchall()
    return SummaryResponse(
        total_customers=int(overall["total_customers"]),
        average_age=round(float(overall["average_age"]), 2),
        average_annual_income_k=round(float(overall["average_annual_income_k"]), 2),
        average_spending_score=round(float(overall["average_spending_score"]), 2),
        by_genre=[
            {
                "genre": row["genre"],
                "count": int(row["count"]),
                "average_age": round(float(row["average_age"]), 2),
                "average_annual_income_k": round(float(row["average_annual_income_k"]), 2),
                "average_spending_score": round(float(row["average_spending_score"]), 2),
            }
            for row in by_genre_rows
        ],
    )
