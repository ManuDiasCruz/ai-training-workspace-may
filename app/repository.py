from __future__ import annotations

from pathlib import Path
from typing import Any

from app.database import connect


SORT_COLUMNS = {
    "customer_id": "customer_id",
    "age": "age",
    "annual_income_k": "annual_income_k",
    "spending_score": "spending_score",
}


def _literal_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_customers(
    database_path: Path | str,
    *,
    page: int,
    page_size: int,
    genre: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_annual_income: int | None = None,
    max_annual_income: int | None = None,
    min_spending_score: int | None = None,
    max_spending_score: int | None = None,
    query: str | None = None,
    sort_by: str = "customer_id",
    sort_order: str = "asc",
) -> tuple[list[dict[str, Any]], int]:
    clauses: list[str] = []
    parameters: list[Any] = []

    filters = (
        ("genre = ?", genre),
        ("age >= ?", min_age),
        ("age <= ?", max_age),
        ("annual_income_k >= ?", min_annual_income),
        ("annual_income_k <= ?", max_annual_income),
        ("spending_score >= ?", min_spending_score),
        ("spending_score <= ?", max_spending_score),
    )
    for clause, value in filters:
        if value is not None:
            clauses.append(clause)
            parameters.append(value)

    if query:
        search_term = f"%{_literal_like(query.casefold())}%"
        clauses.append(
            "(lower(customer_id) LIKE ? ESCAPE '\\' "
            "OR lower(genre) LIKE ? ESCAPE '\\')"
        )
        parameters.extend((search_term, search_term))

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    sort_column = SORT_COLUMNS[sort_by]
    direction = "DESC" if sort_order == "desc" else "ASC"
    offset = (page - 1) * page_size

    with connect(database_path) as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM customers{where}", parameters
        ).fetchone()[0]
        rows = connection.execute(
            f"""
            SELECT customer_id, genre, age, annual_income_k, spending_score
            FROM customers{where}
            ORDER BY {sort_column} {direction}, customer_id ASC
            LIMIT ? OFFSET ?
            """,
            [*parameters, page_size, offset],
        ).fetchall()

    return [dict(row) for row in rows], total


def get_customer(
    database_path: Path | str, customer_id: str
) -> dict[str, Any] | None:
    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT customer_id, genre, age, annual_income_k, spending_score
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()
    return dict(row) if row else None


def customer_count(database_path: Path | str) -> int:
    with connect(database_path) as connection:
        return connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

