"""SQL construction for customer listing, search and statistics.

Every value reaches SQLite through a bound parameter. The only pieces of SQL
built from caller input are the ORDER BY column and direction, and those come
from closed enums (SortField / SortOrder) rather than raw strings.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .models import AgeBracket, Band, Gender, SortField, SortOrder

CUSTOMER_COLUMNS = (
    "id, customer_ref, gender, age, annual_income_k, spending_score, "
    "age_bracket, income_band, spending_tier"
)

# Columns a free-text query is matched against.
SEARCH_COLUMNS = ("customer_ref", "gender", "age_bracket", "income_band", "spending_tier")

LIKE_ESCAPE = "\\"


def escape_like(term: str) -> str:
    """Neutralise LIKE wildcards so a search for '%' means a literal '%'."""
    for char in (LIKE_ESCAPE, "%", "_"):
        term = term.replace(char, LIKE_ESCAPE + char)
    return term


@dataclass
class CustomerFilters:
    """Validated, already-range-checked listing filters."""

    gender: Gender | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_income: int | None = None
    max_income: int | None = None
    min_spending_score: int | None = None
    max_spending_score: int | None = None
    age_bracket: AgeBracket | None = None
    income_band: Band | None = None
    spending_tier: Band | None = None
    q: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """The filters that were actually supplied, for echoing back in the response."""
        result: dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if value is None:
                continue
            result[key] = value.value if hasattr(value, "value") else value
        return result

    def where(self) -> tuple[str, list[Any]]:
        """Build a WHERE clause plus its bound parameters."""
        clauses: list[str] = []
        params: list[Any] = []

        simple = (
            ("gender = ?", self.gender),
            ("age_bracket = ?", self.age_bracket),
            ("income_band = ?", self.income_band),
            ("spending_tier = ?", self.spending_tier),
            ("age >= ?", self.min_age),
            ("age <= ?", self.max_age),
            ("annual_income_k >= ?", self.min_income),
            ("annual_income_k <= ?", self.max_income),
            ("spending_score >= ?", self.min_spending_score),
            ("spending_score <= ?", self.max_spending_score),
        )
        for clause, value in simple:
            if value is None:
                continue
            clauses.append(clause)
            params.append(value.value if hasattr(value, "value") else value)

        if self.q:
            pattern = f"%{escape_like(self.q)}%"
            matches = " OR ".join(f"{column} LIKE ? ESCAPE '{LIKE_ESCAPE}'" for column in SEARCH_COLUMNS)
            clauses.append(f"({matches})")
            params.extend([pattern] * len(SEARCH_COLUMNS))

        if not clauses:
            return "", []
        return " WHERE " + " AND ".join(clauses), params


def count_customers(conn: sqlite3.Connection, filters: CustomerFilters) -> int:
    where, params = filters.where()
    return conn.execute(f"SELECT COUNT(*) FROM customers{where}", params).fetchone()[0]


def list_customers(
    conn: sqlite3.Connection,
    filters: CustomerFilters,
    *,
    limit: int,
    offset: int,
    sort_by: SortField = SortField.id,
    order: SortOrder = SortOrder.asc,
) -> list[sqlite3.Row]:
    where, params = filters.where()
    direction = "ASC" if order is SortOrder.asc else "DESC"
    # sort_by.value and direction are enum-derived, never raw user text.
    sql = (
        f"SELECT {CUSTOMER_COLUMNS} FROM customers{where} "
        f"ORDER BY {sort_by.value} {direction}, id ASC LIMIT ? OFFSET ?"
    )
    return conn.execute(sql, [*params, limit, offset]).fetchall()


def get_customer(conn: sqlite3.Connection, customer_id: int) -> sqlite3.Row | None:
    return conn.execute(
        f"SELECT {CUSTOMER_COLUMNS} FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()


def _group_by(conn: sqlite3.Connection, column: str) -> list[dict[str, Any]]:
    """Group counts for one of the low-cardinality label columns."""
    if column not in {"gender", "income_band", "spending_tier", "age_bracket"}:
        raise ValueError(f"not a groupable column: {column}")
    rows = conn.execute(
        f"""
        SELECT {column} AS value,
               COUNT(*) AS count,
               ROUND(AVG(spending_score), 2) AS avg_spending_score
        FROM customers
        GROUP BY {column}
        ORDER BY value
        """
    ).fetchall()
    return [dict(row) for row in rows]


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    totals = conn.execute(
        """
        SELECT COUNT(*)                       AS total_customers,
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

    return {
        "total_customers": totals["total_customers"],
        "age": {"min": totals["age_min"], "max": totals["age_max"], "avg": totals["age_avg"]},
        "annual_income_k": {
            "min": totals["income_min"],
            "max": totals["income_max"],
            "avg": totals["income_avg"],
        },
        "spending_score": {
            "min": totals["score_min"],
            "max": totals["score_max"],
            "avg": totals["score_avg"],
        },
        "by_gender": _group_by(conn, "gender"),
        "by_income_band": _group_by(conn, "income_band"),
        "by_spending_tier": _group_by(conn, "spending_tier"),
        "by_age_bracket": _group_by(conn, "age_bracket"),
    }
