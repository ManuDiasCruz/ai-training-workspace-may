"""Parameterized database queries for the customer resource."""

from __future__ import annotations

import math
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


def _where(filters: CustomerFilters) -> tuple[str, list[object]]:
    clauses: list[str] = []
    parameters: list[object] = []

    for field, operator, value in (
        ("gender", "=", filters.gender),
        ("age", ">=", filters.min_age),
        ("age", "<=", filters.max_age),
        ("annual_income_k", ">=", filters.min_income),
        ("annual_income_k", "<=", filters.max_income),
        ("spending_score", ">=", filters.min_spending_score),
        ("spending_score", "<=", filters.max_spending_score),
    ):
        if value is not None:
            clauses.append(f"{field} {operator} ?")
            parameters.append(value)

    if filters.query:
        term = f"%{filters.query.lower()}%"
        clauses.append(
            "(" 
            "LOWER(customer_id) LIKE ? OR LOWER(gender) LIKE ? OR "
            "CAST(age AS TEXT) LIKE ? OR CAST(annual_income_k AS TEXT) LIKE ? OR "
            "CAST(spending_score AS TEXT) LIKE ?"
            ")"
        )
        parameters.extend([term] * 5)

    return (f" WHERE {' AND '.join(clauses)}" if clauses else "", parameters)


def list_customers(
    connection: sqlite3.Connection,
    filters: CustomerFilters,
    page: int,
    page_size: int,
) -> dict[str, object]:
    where_sql, parameters = _where(filters)
    total = connection.execute(
        f"SELECT COUNT(*) FROM customers{where_sql}", parameters
    ).fetchone()[0]
    rows = connection.execute(
        f"""
        SELECT customer_id, gender, age, annual_income_k, spending_score
        FROM customers{where_sql}
        ORDER BY customer_id
        LIMIT ? OFFSET ?
        """,
        [*parameters, page_size, (page - 1) * page_size],
    ).fetchall()
    return {
        "items": [dict(row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


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
