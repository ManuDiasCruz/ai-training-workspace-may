"""Data access layer.

All SQL lives here. Every value reaching SQLite goes through a bound parameter;
identifiers (sort columns) are resolved through an allow-list, so no user input
is ever interpolated into a statement.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .models import CustomerListQuery

#: Public sort key -> physical column. Also acts as the allow-list that keeps
#: `sort_by` out of string interpolation risk.
_SORT_COLUMNS: dict[str, str] = {
    # customer_id is zero-padded text, so sorting it lexicographically and
    # numerically agree; use the integer key, which is the primary key.
    "customer_id": "id",
    "age": "age",
    "annual_income_k": "annual_income_k",
    "spending_score": "spending_score",
}

_SELECT_FIELDS = (
    "customer_id, gender, age, annual_income_k, spending_score, segment"
)

_LIKE_ESCAPE = "\\"


def _escape_like(term: str) -> str:
    """Neutralise LIKE wildcards in user input.

    Without this, a search for '%' would match every row and '_' would act as a
    single-character wildcard instead of a literal underscore.
    """
    out = term.replace(_LIKE_ESCAPE, _LIKE_ESCAPE * 2)
    for wildcard in ("%", "_"):
        out = out.replace(wildcard, _LIKE_ESCAPE + wildcard)
    return out


def _build_filters(query: CustomerListQuery) -> tuple[str, dict[str, Any]]:
    """Translate validated query params into a WHERE clause + bound params."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    simple_equals = (("gender", query.gender), ("segment", query.segment))
    for column, value in simple_equals:
        if value is not None:
            clauses.append(f"{column} = :{column}")
            params[column] = value

    ranges = (
        ("age", ">=", "age_min", query.age_min),
        ("age", "<=", "age_max", query.age_max),
        ("annual_income_k", ">=", "income_min", query.income_min),
        ("annual_income_k", "<=", "income_max", query.income_max),
        ("spending_score", ">=", "score_min", query.score_min),
        ("spending_score", "<=", "score_max", query.score_max),
    )
    for column, operator, name, value in ranges:
        if value is not None:
            clauses.append(f"{column} {operator} :{name}")
            params[name] = value

    if query.q:
        term = query.q.strip()
        if term:
            # Basic search: the dataset has no free-text column, so the only
            # meaningful targets are the identifier and the gender label.
            clauses.append(
                f"(customer_id LIKE :q ESCAPE '{_LIKE_ESCAPE}'"
                f" OR gender LIKE :q ESCAPE '{_LIKE_ESCAPE}')"
            )
            params["q"] = f"%{_escape_like(term)}%"

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def count_customers(conn: sqlite3.Connection, query: CustomerListQuery) -> int:
    where, params = _build_filters(query)
    sql = f"SELECT COUNT(*) AS n FROM customers_enriched{where}"
    return int(conn.execute(sql, params).fetchone()["n"])


def list_customers(
    conn: sqlite3.Connection, query: CustomerListQuery
) -> list[dict[str, Any]]:
    where, params = _build_filters(query)
    sort_column = _SORT_COLUMNS[query.sort_by]
    direction = "DESC" if query.order == "desc" else "ASC"

    # `id` is appended as a tiebreaker so pagination is deterministic when the
    # primary sort key has duplicates (e.g. many customers share an age).
    sql = (
        f"SELECT {_SELECT_FIELDS} FROM customers_enriched{where}"
        f" ORDER BY {sort_column} {direction}, id ASC"
        " LIMIT :limit OFFSET :offset"
    )
    params["limit"] = query.page_size
    params["offset"] = (query.page - 1) * query.page_size
    return [dict(row) for row in conn.execute(sql, params)]


def get_customer(conn: sqlite3.Connection, numeric_id: int) -> dict[str, Any] | None:
    sql = f"SELECT {_SELECT_FIELDS} FROM customers_enriched WHERE id = :id"
    row = conn.execute(sql, {"id": numeric_id}).fetchone()
    return dict(row) if row else None


def record_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) AS n FROM customers").fetchone()["n"])


def import_metadata(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT source_file, source_sha256, row_count, imported_at"
        " FROM import_metadata WHERE id = 1"
    ).fetchone()
    return dict(row) if row else None


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    """Aggregate summary over the whole dataset."""
    totals = conn.execute(
        """
        SELECT COUNT(*)                AS total_customers,
               MIN(age)                AS age_min,
               MAX(age)                AS age_max,
               AVG(age)                AS age_avg,
               MIN(annual_income_k)    AS income_min,
               MAX(annual_income_k)    AS income_max,
               AVG(annual_income_k)    AS income_avg,
               MIN(spending_score)     AS score_min,
               MAX(spending_score)     AS score_max,
               AVG(spending_score)     AS score_avg
        FROM customers
        """
    ).fetchone()

    by_gender = conn.execute(
        """
        SELECT gender,
               COUNT(*)             AS count,
               AVG(age)             AS avg_age,
               AVG(annual_income_k) AS avg_annual_income_k,
               AVG(spending_score)  AS avg_spending_score
        FROM customers
        GROUP BY gender
        ORDER BY gender
        """
    ).fetchall()

    by_segment = conn.execute(
        """
        SELECT segment,
               COUNT(*)             AS count,
               AVG(annual_income_k) AS avg_annual_income_k,
               AVG(spending_score)  AS avg_spending_score
        FROM customers_enriched
        GROUP BY segment
        ORDER BY count DESC, segment ASC
        """
    ).fetchall()

    def rounded(row: sqlite3.Row, keys: tuple[str, ...]) -> dict[str, Any]:
        return {k: round(row[k], 2) if isinstance(row[k], float) else row[k] for k in keys}

    if totals["total_customers"] == 0:
        # MIN/MAX/AVG are NULL over an empty table; report zeros rather than
        # letting round(None) raise.
        empty = {"min": 0, "max": 0, "avg": 0.0}
        return {
            "total_customers": 0,
            "age": dict(empty),
            "annual_income_k": dict(empty),
            "spending_score": dict(empty),
            "by_gender": [],
            "by_segment": [],
        }

    return {
        "total_customers": totals["total_customers"],
        "age": {
            "min": totals["age_min"],
            "max": totals["age_max"],
            "avg": round(totals["age_avg"], 2),
        },
        "annual_income_k": {
            "min": totals["income_min"],
            "max": totals["income_max"],
            "avg": round(totals["income_avg"], 2),
        },
        "spending_score": {
            "min": totals["score_min"],
            "max": totals["score_max"],
            "avg": round(totals["score_avg"], 2),
        },
        "by_gender": [
            rounded(
                r,
                (
                    "gender",
                    "count",
                    "avg_age",
                    "avg_annual_income_k",
                    "avg_spending_score",
                ),
            )
            for r in by_gender
        ],
        "by_segment": [
            rounded(
                r, ("segment", "count", "avg_annual_income_k", "avg_spending_score")
            )
            for r in by_segment
        ],
    }
