from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerFilters:
    gender: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    query: str | None = None


def _build_where(filters: CustomerFilters) -> tuple[str, list[object]]:
    clauses: list[str] = []
    parameters: list[object] = []

    filter_mappings = [
        ("gender = ?", filters.gender),
        ("age >= ?", filters.min_age),
        ("age <= ?", filters.max_age),
        ("annual_income_k >= ?", filters.min_income),
        ("annual_income_k <= ?", filters.max_income),
        ("spending_score >= ?", filters.min_spending_score),
        ("spending_score <= ?", filters.max_spending_score),
    ]
    for clause, value in filter_mappings:
        if value is not None:
            clauses.append(clause)
            parameters.append(value)

    if filters.query:
        clauses.append(
            "(" 
            "customer_id LIKE ? OR "
            "LOWER(gender) LIKE ? OR "
            "CAST(age AS TEXT) LIKE ? OR "
            "CAST(annual_income_k AS TEXT) LIKE ? OR "
            "CAST(spending_score AS TEXT) LIKE ?"
            ")"
        )
        pattern = f"%{filters.query.lower()}%"
        parameters.extend([pattern] * 5)

    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, parameters


def list_customers(
    connection: sqlite3.Connection,
    filters: CustomerFilters,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, object]], int]:
    where_sql, parameters = _build_where(filters)
    total = connection.execute(
        f"SELECT COUNT(*) FROM customers{where_sql}", parameters
    ).fetchone()[0]
    offset = (page - 1) * page_size
    rows = connection.execute(
        f"""
        SELECT customer_id, gender, age, annual_income_k, spending_score
        FROM customers
        {where_sql}
        ORDER BY customer_id
        LIMIT ? OFFSET ?
        """,
        [*parameters, page_size, offset],
    ).fetchall()
    return [dict(row) for row in rows], total


def get_customer(connection: sqlite3.Connection, customer_id: str) -> dict[str, object] | None:
    row = connection.execute(
        """
        SELECT customer_id, gender, age, annual_income_k, spending_score
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()
    return dict(row) if row else None

