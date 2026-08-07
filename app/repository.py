"""Data access layer.

All SQL lives here. Values always travel as bound parameters; the only text
interpolated into a statement is a column name that has already been
validated by the SortField enum, or an integer constant defined in this
codebase.
"""

from __future__ import annotations

import sqlite3

from app.models import SEGMENT_BOUNDS, CustomerQuery

CUSTOMER_COLUMNS = "customer_id, genre, age, annual_income_k, spending_score"

# Backslash-escaped LIKE, so a literal % or _ in a search term is matched as
# itself instead of acting as a wildcard.
_LIKE_ESCAPE = "\\"


def _like_pattern(term: str) -> str:
    escaped = (
        term.replace(_LIKE_ESCAPE, _LIKE_ESCAPE * 2)
        .replace("%", f"{_LIKE_ESCAPE}%")
        .replace("_", f"{_LIKE_ESCAPE}_")
    )
    return f"%{escaped}%"


def _build_filters(query: CustomerQuery) -> tuple[str, list[object]]:
    """Translate validated query parameters into a WHERE clause."""
    clauses: list[str] = []
    params: list[object] = []

    simple_bounds = (
        ("genre", "=", query.genre.value if query.genre else None),
        ("age", ">=", query.min_age),
        ("age", "<=", query.max_age),
        ("annual_income_k", ">=", query.min_income),
        ("annual_income_k", "<=", query.max_income),
        ("spending_score", ">=", query.min_score),
        ("spending_score", "<=", query.max_score),
    )
    for column, operator, value in simple_bounds:
        if value is not None:
            clauses.append(f"{column} {operator} ?")
            params.append(value)

    if query.q:
        # SQLite's LIKE is case-insensitive for ASCII, which is what gives
        # ?q=female its case-insensitive behaviour for free.
        pattern = _like_pattern(query.q.strip())
        clauses.append(
            f"(customer_id LIKE ? ESCAPE '{_LIKE_ESCAPE}' "
            f"OR genre LIKE ? ESCAPE '{_LIKE_ESCAPE}')"
        )
        params.extend([pattern, pattern])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def count_customers(conn: sqlite3.Connection, query: CustomerQuery) -> int:
    where, params = _build_filters(query)
    return conn.execute(f"SELECT COUNT(*) FROM customers {where}", params).fetchone()[0]


def list_customers(conn: sqlite3.Connection, query: CustomerQuery) -> list[sqlite3.Row]:
    where, params = _build_filters(query)

    # query.sort_by is a SortField enum member, so its value is one of a fixed
    # set of known column names -- never caller-supplied text.
    direction = "DESC" if query.order.value == "desc" else "ASC"
    # customer_id breaks ties so paging over a non-unique sort key (age, genre)
    # is stable and cannot repeat or skip a record between pages.
    order_by = f"ORDER BY {query.sort_by.value} {direction}, customer_id ASC"

    return conn.execute(
        f"SELECT {CUSTOMER_COLUMNS} FROM customers {where} {order_by} LIMIT ? OFFSET ?",
        [*params, query.page_size, query.offset],
    ).fetchall()


def get_customer(conn: sqlite3.Connection, customer_id: str) -> sqlite3.Row | None:
    """Fetch one customer. The identifier is zero-padded to the stored width,
    so both `1` and `0001` resolve to the same record."""
    return conn.execute(
        f"SELECT {CUSTOMER_COLUMNS} FROM customers WHERE customer_id = ?",
        (customer_id.zfill(4),),
    ).fetchone()


def _numeric_summary(conn: sqlite3.Connection, column: str) -> dict[str, float]:
    """Min/max/mean for one numeric column. `column` is a module constant."""
    row = conn.execute(
        f"SELECT MIN({column}) AS lo, MAX({column}) AS hi, AVG({column}) AS mean FROM customers"
    ).fetchone()
    return {"min": row["lo"], "max": row["hi"], "mean": round(row["mean"], 2)}


def _segment_case_sql() -> str:
    """Build the CASE expression from SEGMENT_BOUNDS so the band definitions
    have a single source of truth shared with the response model."""
    branches = " ".join(
        f"WHEN spending_score BETWEEN {low} AND {high} THEN '{name}'"
        for name, (low, high) in SEGMENT_BOUNDS.items()
    )
    return f"CASE {branches} END"


def dataset_stats(conn: sqlite3.Connection) -> dict[str, object]:
    """Aggregate summary of the whole dataset."""
    total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    if total == 0:
        empty = {"min": 0, "max": 0, "mean": 0.0}
        return {
            "total_customers": 0,
            "genre_breakdown": [],
            "age": empty,
            "annual_income_k": empty,
            "spending_score": empty,
            "spending_segments": [],
            "last_import": last_import(conn),
        }

    genre_rows = conn.execute(
        """
        SELECT genre,
               COUNT(*)              AS count,
               AVG(age)              AS mean_age,
               AVG(annual_income_k)  AS mean_income,
               AVG(spending_score)   AS mean_score
        FROM customers
        GROUP BY genre
        ORDER BY count DESC, genre ASC
        """
    ).fetchall()

    genre_breakdown = [
        {
            "genre": row["genre"],
            "count": row["count"],
            "share_pct": round(row["count"] * 100.0 / total, 2),
            "mean_age": round(row["mean_age"], 2),
            "mean_annual_income_k": round(row["mean_income"], 2),
            "mean_spending_score": round(row["mean_score"], 2),
        }
        for row in genre_rows
    ]

    segment_rows = conn.execute(
        f"""
        SELECT {_segment_case_sql()} AS segment,
               COUNT(*)             AS count,
               AVG(annual_income_k) AS mean_income
        FROM customers
        GROUP BY segment
        """
    ).fetchall()
    counts = {row["segment"]: row for row in segment_rows}

    # Emit every band in a fixed order, including any with no members, so the
    # response shape does not change with the data.
    spending_segments = [
        {
            "segment": name,
            "score_range": f"{low}-{high}",
            "count": counts[name]["count"] if name in counts else 0,
            "mean_annual_income_k": (
                round(counts[name]["mean_income"], 2) if name in counts else 0.0
            ),
        }
        for name, (low, high) in SEGMENT_BOUNDS.items()
    ]

    return {
        "total_customers": total,
        "genre_breakdown": genre_breakdown,
        "age": _numeric_summary(conn, "age"),
        "annual_income_k": _numeric_summary(conn, "annual_income_k"),
        "spending_score": _numeric_summary(conn, "spending_score"),
        "spending_segments": spending_segments,
        "last_import": last_import(conn),
    }


def last_import(conn: sqlite3.Connection) -> dict[str, object] | None:
    """Most recent importer run, or None if the table is absent/empty (which
    happens if the database was populated by something other than the
    importer)."""
    try:
        row = conn.execute(
            """
            SELECT source_file, source_sha256, row_count, imported_at
            FROM import_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    return dict(row) if row else None
