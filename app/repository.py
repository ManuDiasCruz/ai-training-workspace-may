from __future__ import annotations

import sqlite3
from dataclasses import dataclass


SORT_FIELDS = {
    "customer_id": "customer_id",
    "age": "age",
    "annual_income_k": "annual_income_k",
    "spending_score": "spending_score",
}


@dataclass(frozen=True)
class CustomerFilters:
    genre: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    q: str | None = None


def _row_to_customer(row: sqlite3.Row) -> dict[str, object]:
    return {
        "customer_id": row["customer_id"],
        "genre": row["genre"],
        "age": row["age"],
        "annual_income_k": row["annual_income_k"],
        "spending_score": row["spending_score"],
    }


def _build_where_clause(filters: CustomerFilters) -> tuple[str, dict[str, object]]:
    clauses: list[str] = []
    params: dict[str, object] = {}

    if filters.genre:
        clauses.append("genre = :genre")
        params["genre"] = filters.genre
    if filters.min_age is not None:
        clauses.append("age >= :min_age")
        params["min_age"] = filters.min_age
    if filters.max_age is not None:
        clauses.append("age <= :max_age")
        params["max_age"] = filters.max_age
    if filters.min_income is not None:
        clauses.append("annual_income_k >= :min_income")
        params["min_income"] = filters.min_income
    if filters.max_income is not None:
        clauses.append("annual_income_k <= :max_income")
        params["max_income"] = filters.max_income
    if filters.min_spending_score is not None:
        clauses.append("spending_score >= :min_spending_score")
        params["min_spending_score"] = filters.min_spending_score
    if filters.max_spending_score is not None:
        clauses.append("spending_score <= :max_spending_score")
        params["max_spending_score"] = filters.max_spending_score
    if filters.q:
        clauses.append(
            """
            (
                lower(customer_id) LIKE :search
                OR lower(genre) LIKE :search
                OR CAST(age AS TEXT) LIKE :search
                OR CAST(annual_income_k AS TEXT) LIKE :search
                OR CAST(spending_score AS TEXT) LIKE :search
            )
            """
        )
        params["search"] = f"%{filters.q.casefold()}%"

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params


def list_customers(
    connection: sqlite3.Connection,
    filters: CustomerFilters,
    page: int,
    per_page: int,
    sort_by: str,
    sort_order: str,
) -> tuple[list[dict[str, object]], int]:
    where_sql, params = _build_where_clause(filters)
    total_row = connection.execute(
        f"SELECT COUNT(*) AS total FROM shopping_customers {where_sql}",
        params,
    ).fetchone()
    total = int(total_row["total"])

    sort_column = SORT_FIELDS[sort_by]
    direction = "DESC" if sort_order == "desc" else "ASC"
    params["limit"] = per_page
    params["offset"] = (page - 1) * per_page
    rows = connection.execute(
        f"""
        SELECT customer_id, genre, age, annual_income_k, spending_score
        FROM shopping_customers
        {where_sql}
        ORDER BY {sort_column} {direction}, customer_id ASC
        LIMIT :limit OFFSET :offset
        """,
        params,
    ).fetchall()
    return [_row_to_customer(row) for row in rows], total


def get_customer(connection: sqlite3.Connection, customer_id: str) -> dict[str, object] | None:
    row = connection.execute(
        """
        SELECT customer_id, genre, age, annual_income_k, spending_score
        FROM shopping_customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()
    return _row_to_customer(row) if row else None


def get_dataset_stats(connection: sqlite3.Connection) -> dict[str, object]:
    row = connection.execute(
        """
        SELECT
            COUNT(*) AS total_records,
            MIN(age) AS age_min,
            MAX(age) AS age_max,
            MIN(annual_income_k) AS annual_income_k_min,
            MAX(annual_income_k) AS annual_income_k_max,
            MIN(spending_score) AS spending_score_min,
            MAX(spending_score) AS spending_score_max
        FROM shopping_customers
        """
    ).fetchone()
    genre_rows = connection.execute(
        """
        SELECT genre, COUNT(*) AS total
        FROM shopping_customers
        GROUP BY genre
        ORDER BY genre
        """
    ).fetchall()
    return {
        "total_records": row["total_records"],
        "genres": {genre_row["genre"]: genre_row["total"] for genre_row in genre_rows},
        "age_min": row["age_min"],
        "age_max": row["age_max"],
        "annual_income_k_min": row["annual_income_k_min"],
        "annual_income_k_max": row["annual_income_k_max"],
        "spending_score_min": row["spending_score_min"],
        "spending_score_max": row["spending_score_max"],
    }

