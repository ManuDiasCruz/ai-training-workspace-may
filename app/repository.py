"""Parameterized SQLite queries for customer records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.database import connect


def _build_where(
    *,
    gender: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_income: int | None = None,
    max_income: int | None = None,
    min_spending_score: int | None = None,
    max_spending_score: int | None = None,
    search: str | None = None,
) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    parameters: list[Any] = []

    filters = (
        ("gender = ?", gender),
        ("age >= ?", min_age),
        ("age <= ?", max_age),
        ("annual_income_k >= ?", min_income),
        ("annual_income_k <= ?", max_income),
        ("spending_score >= ?", min_spending_score),
        ("spending_score <= ?", max_spending_score),
    )
    for condition, value in filters:
        if value is not None:
            conditions.append(condition)
            parameters.append(value)

    if search:
        # Treat LIKE metacharacters as text so search behavior is predictable.
        escaped = search.lower().replace("\\", "\\\\").replace("%", "\\%")
        escaped = escaped.replace("_", "\\_")
        pattern = f"%{escaped}%"
        conditions.append(
            "(LOWER(customer_id) LIKE ? ESCAPE '\\' "
            "OR LOWER(gender) LIKE ? ESCAPE '\\')"
        )
        parameters.extend((pattern, pattern))

    if not conditions:
        return "", parameters
    return " WHERE " + " AND ".join(conditions), parameters


def list_customers(
    database_path: str | Path,
    *,
    page: int,
    page_size: int,
    **filters: Any,
) -> tuple[list[dict[str, Any]], int]:
    """Return a deterministic page plus the total matching row count."""

    where_sql, parameters = _build_where(**filters)
    offset = (page - 1) * page_size
    query = (
        "SELECT customer_id, gender, age, annual_income_k, spending_score "
        f"FROM customers{where_sql} "
        "ORDER BY customer_id LIMIT ? OFFSET ?"
    )

    with connect(database_path) as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM customers{where_sql}", parameters
        ).fetchone()[0]
        rows = connection.execute(query, [*parameters, page_size, offset]).fetchall()

    return [dict(row) for row in rows], total


def get_customer(database_path: str | Path, customer_id: str) -> dict[str, Any] | None:
    """Return one customer by source ID."""

    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT customer_id, gender, age, annual_income_k, spending_score
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()
    return dict(row) if row else None


def count_customers(database_path: str | Path) -> int:
    """Count all persisted customers."""

    with connect(database_path) as connection:
        return connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

