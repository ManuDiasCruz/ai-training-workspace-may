"""Data-access layer: every SQL query against the customers table lives here.

All values are bound as parameters; the only string interpolation is the
ORDER BY clause, which is restricted to a whitelist of column names.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

SORTABLE_FIELDS = ("customer_id", "genre", "age", "annual_income_k", "spending_score")


@dataclass(frozen=True)
class CustomerFilters:
    """Optional constraints applied to list/count queries."""

    genre: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_score: int | None = None
    max_score: int | None = None
    q: str | None = None


def _build_where(filters: CustomerFilters) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []

    range_conditions = (
        ("genre = ?", filters.genre),
        ("age >= ?", filters.min_age),
        ("age <= ?", filters.max_age),
        ("annual_income_k >= ?", filters.min_income),
        ("annual_income_k <= ?", filters.max_income),
        ("spending_score >= ?", filters.min_score),
        ("spending_score <= ?", filters.max_score),
    )
    for clause, value in range_conditions:
        if value is not None:
            clauses.append(clause)
            params.append(value)

    if filters.q:
        # Search semantics: substring match on the zero-padded customer ID
        # (the format used in the CSV) or case-insensitive prefix match on
        # the genre. A prefix match avoids the substring trap where "male"
        # would also match every "Female" row.
        clauses.append("(printf('%04d', customer_id) LIKE ? ESCAPE '\\' OR lower(genre) LIKE ? ESCAPE '\\')")
        escaped = filters.q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params.extend([f"%{escaped}%", f"{escaped}%"])

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def count_customers(conn: sqlite3.Connection, filters: CustomerFilters) -> int:
    where, params = _build_where(filters)
    row = conn.execute(f"SELECT COUNT(*) AS n FROM customers{where}", params).fetchone()
    return row["n"]


def list_customers(
    conn: sqlite3.Connection,
    filters: CustomerFilters,
    sort_by: str = "customer_id",
    sort_order: str = "asc",
    limit: int = 20,
    offset: int = 0,
) -> list[sqlite3.Row]:
    if sort_by not in SORTABLE_FIELDS:
        raise ValueError(f"unsortable field: {sort_by}")
    if sort_order not in ("asc", "desc"):
        raise ValueError(f"invalid sort order: {sort_order}")

    where, params = _build_where(filters)
    sql = (
        "SELECT customer_id, genre, age, annual_income_k, spending_score"
        f" FROM customers{where}"
        f" ORDER BY {sort_by} {sort_order.upper()}, customer_id ASC"
        " LIMIT ? OFFSET ?"
    )
    return conn.execute(sql, [*params, limit, offset]).fetchall()


def get_customer(conn: sqlite3.Connection, customer_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT customer_id, genre, age, annual_income_k, spending_score"
        " FROM customers WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()


def get_stats(conn: sqlite3.Connection) -> dict:
    summary = conn.execute(
        """
        SELECT COUNT(*)                       AS total,
               MIN(age)                       AS age_min,
               MAX(age)                       AS age_max,
               ROUND(AVG(age), 2)             AS age_avg,
               MIN(annual_income_k)           AS income_min,
               MAX(annual_income_k)           AS income_max,
               ROUND(AVG(annual_income_k), 2) AS income_avg,
               MIN(spending_score)            AS score_min,
               MAX(spending_score)            AS score_max,
               ROUND(AVG(spending_score), 2)  AS score_avg
        FROM customers
        """
    ).fetchone()

    genre_rows = conn.execute(
        "SELECT genre, COUNT(*) AS n FROM customers GROUP BY genre ORDER BY genre"
    ).fetchall()

    return {
        "total_customers": summary["total"],
        "genre_counts": {row["genre"]: row["n"] for row in genre_rows},
        "age": {"min": summary["age_min"], "max": summary["age_max"], "avg": summary["age_avg"]},
        "annual_income_k": {
            "min": summary["income_min"],
            "max": summary["income_max"],
            "avg": summary["income_avg"],
        },
        "spending_score": {
            "min": summary["score_min"],
            "max": summary["score_max"],
            "avg": summary["score_avg"],
        },
    }
