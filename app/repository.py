"""Parameterized read operations for customer records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.database import connect


@dataclass(frozen=True)
class CustomerFilters:
    gender: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_annual_income: int | None = None
    max_annual_income: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    search: str | None = None


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_where(filters: CustomerFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    parameters: list[Any] = []

    field_filters = [
        ("gender = ?", filters.gender),
        ("age >= ?", filters.min_age),
        ("age <= ?", filters.max_age),
        ("annual_income_kusd >= ?", filters.min_annual_income),
        ("annual_income_kusd <= ?", filters.max_annual_income),
        ("spending_score >= ?", filters.min_spending_score),
        ("spending_score <= ?", filters.max_spending_score),
    ]
    for clause, value in field_filters:
        if value is not None:
            clauses.append(clause)
            parameters.append(value)

    if filters.search:
        pattern = f"%{_escape_like(filters.search.strip())}%"
        clauses.append(
            "(customer_id LIKE ? ESCAPE '\\' COLLATE NOCASE "
            "OR gender LIKE ? ESCAPE '\\' COLLATE NOCASE)"
        )
        parameters.extend([pattern, pattern])

    return (f"WHERE {' AND '.join(clauses)}" if clauses else "", parameters)


def list_customers(
    database_path: str | Path,
    filters: CustomerFilters,
    *,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """Return a stable page of matching customers and the match count."""

    where_clause, parameters = _build_where(filters)
    offset = (page - 1) * page_size

    with connect(database_path) as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM customers {where_clause}", parameters
        ).fetchone()[0]
        rows = connection.execute(
            f"""
            SELECT customer_id, gender, age, annual_income_kusd, spending_score
            FROM customers
            {where_clause}
            ORDER BY customer_id ASC
            LIMIT ? OFFSET ?
            """,
            [*parameters, page_size, offset],
        ).fetchall()

    return [dict(row) for row in rows], total


def get_customer(database_path: str | Path, customer_id: str) -> dict[str, Any] | None:
    """Return one customer by exact ID, if present."""

    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT customer_id, gender, age, annual_income_kusd, spending_score
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()
    return dict(row) if row else None
