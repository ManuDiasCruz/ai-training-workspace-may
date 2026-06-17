"""Customer read queries with parameterized filters."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .database import connection


@dataclass(frozen=True)
class CustomerFilters:
    genre: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    query: str | None = None


def _where(filters: CustomerFilters) -> tuple[str, list[str | int]]:
    clauses: list[str] = []
    parameters: list[str | int] = []
    mappings = (
        ("genre = ? COLLATE NOCASE", filters.genre),
        ("age >= ?", filters.min_age),
        ("age <= ?", filters.max_age),
        ("annual_income_k >= ?", filters.min_income),
        ("annual_income_k <= ?", filters.max_income),
        ("spending_score >= ?", filters.min_spending_score),
        ("spending_score <= ?", filters.max_spending_score),
    )
    for clause, value in mappings:
        if value is not None:
            clauses.append(clause)
            parameters.append(value)
    if filters.query is not None:
        clauses.append("(customer_id LIKE ? ESCAPE '\\' OR genre LIKE ? ESCAPE '\\')")
        escaped = filters.query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        parameters.extend((f"%{escaped}%", f"%{escaped}%"))
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), parameters


def list_customers(
    database: Path, filters: CustomerFilters, page: int, page_size: int
) -> tuple[list[sqlite3.Row], int]:
    where_sql, parameters = _where(filters)
    offset = (page - 1) * page_size
    with connection(database) as db:
        count = db.execute(
            f"SELECT COUNT(*) AS count FROM customers{where_sql}", parameters
        ).fetchone()["count"]
        rows = db.execute(
            f"""
            SELECT customer_id, genre, age, annual_income_k, spending_score
            FROM customers{where_sql}
            ORDER BY customer_id
            LIMIT ? OFFSET ?
            """,
            [*parameters, page_size, offset],
        ).fetchall()
    return rows, int(count)


def get_customer(database: Path, customer_id: str) -> sqlite3.Row | None:
    with connection(database) as db:
        return db.execute(
            """
            SELECT customer_id, genre, age, annual_income_k, spending_score
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()
