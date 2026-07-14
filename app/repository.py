"""Parameterized queries for customer data."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerFilters:
    gender: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    income_min: int | None = None
    income_max: int | None = None
    score_min: int | None = None
    score_max: int | None = None
    search: str | None = None


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _where_clause(filters: CustomerFilters) -> tuple[str, list[object]]:
    clauses: list[str] = []
    parameters: list[object] = []

    comparisons = (
        ("gender = ? COLLATE NOCASE", filters.gender),
        ("age >= ?", filters.age_min),
        ("age <= ?", filters.age_max),
        ("annual_income_kusd >= ?", filters.income_min),
        ("annual_income_kusd <= ?", filters.income_max),
        ("spending_score >= ?", filters.score_min),
        ("spending_score <= ?", filters.score_max),
    )
    for clause, value in comparisons:
        if value is not None:
            clauses.append(clause)
            parameters.append(value)

    if filters.search:
        clauses.append(
            "(LOWER(customer_id) LIKE ? ESCAPE '\\' "
            "OR LOWER(gender) LIKE ? ESCAPE '\\')"
        )
        pattern = f"%{_escape_like(filters.search.lower())}%"
        parameters.extend((pattern, pattern))

    if not clauses:
        return "", parameters
    return " WHERE " + " AND ".join(clauses), parameters


def count_customers(
    connection: sqlite3.Connection, filters: CustomerFilters | None = None
) -> int:
    where, parameters = _where_clause(filters or CustomerFilters())
    row = connection.execute(
        "SELECT COUNT(*) FROM customers" + where,
        parameters,
    ).fetchone()
    return int(row[0])


def list_customers(
    connection: sqlite3.Connection,
    filters: CustomerFilters,
    *,
    limit: int,
    offset: int,
) -> list[sqlite3.Row]:
    where, parameters = _where_clause(filters)
    return connection.execute(
        """
        SELECT customer_id, gender, age, annual_income_kusd, spending_score
        FROM customers
        """
        + where
        + " ORDER BY customer_id ASC LIMIT ? OFFSET ?",
        [*parameters, limit, offset],
    ).fetchall()


def get_customer(
    connection: sqlite3.Connection, customer_id: str
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT customer_id, gender, age, annual_income_kusd, spending_score
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()
