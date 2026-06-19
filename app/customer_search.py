"""SQLite FTS5 search projection for customer data.

This module deliberately keeps search storage separate from the SQLAlchemy
``customers`` table.  FTS rows are copied into a content-bearing virtual table
and three database triggers update that projection atomically whenever a
customer changes.  Keeping the search table self-contained makes index
rebuilding explicit and allows the search query to use weighted BM25 ranking
without coupling the API to SQLite's external-content table conventions.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from .models import Customer
from .schemas import CustomerOut, CustomerPage, PageMeta

SEARCH_TABLE = "customer_search"
SEARCH_COLUMNS = (
    "customer_id",
    "genre",
    "age",
    "annual_income_k",
    "spending_score",
)


class SearchIndexUnavailable(RuntimeError):
    """Raised when the current database cannot provide the FTS5 index."""


@dataclass(frozen=True)
class SearchIndexStatus:
    enabled: bool
    indexed_rows: int


def _fts5_supported(conn: Connection) -> bool:
    """Probe FTS5 directly because SQLite compile flags are not authoritative."""
    try:
        conn.exec_driver_sql(
            "CREATE VIRTUAL TABLE IF NOT EXISTS temp._customer_fts_probe USING fts5(value)"
        )
        conn.exec_driver_sql("DROP TABLE IF EXISTS temp._customer_fts_probe")
        return True
    except Exception:  # SQLite builds without the FTS5 module
        return False


def _create_schema(conn: Connection) -> None:
    columns = ", ".join(SEARCH_COLUMNS)
    conn.exec_driver_sql(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS {SEARCH_TABLE} "
        f"USING fts5({columns}, tokenize='unicode61 remove_diacritics 2')"
    )
    new_values = ", ".join(f"new.{column}" for column in SEARCH_COLUMNS)
    conn.exec_driver_sql(
        f"CREATE TRIGGER IF NOT EXISTS customer_search_insert "
        f"AFTER INSERT ON customers BEGIN "
        f"INSERT INTO {SEARCH_TABLE}(rowid, {columns}) VALUES (new.id, {new_values}); "
        "END"
    )
    conn.exec_driver_sql(
        f"CREATE TRIGGER IF NOT EXISTS customer_search_delete "
        f"AFTER DELETE ON customers BEGIN "
        f"DELETE FROM {SEARCH_TABLE} WHERE rowid = old.id; "
        "END"
    )
    conn.exec_driver_sql(
        f"CREATE TRIGGER IF NOT EXISTS customer_search_update "
        f"AFTER UPDATE ON customers BEGIN "
        f"DELETE FROM {SEARCH_TABLE} WHERE rowid = old.id; "
        f"INSERT INTO {SEARCH_TABLE}(rowid, {columns}) VALUES (new.id, {new_values}); "
        "END"
    )


def rebuild_index(conn: Connection) -> SearchIndexStatus:
    """Create the index and fully replace its contents from ``customers``."""
    if conn.dialect.name != "sqlite" or not _fts5_supported(conn):
        return SearchIndexStatus(enabled=False, indexed_rows=0)

    _create_schema(conn)
    columns = ", ".join(SEARCH_COLUMNS)
    conn.exec_driver_sql(f"DELETE FROM {SEARCH_TABLE}")
    conn.exec_driver_sql(
        f"INSERT INTO {SEARCH_TABLE}(rowid, {columns}) "
        f"SELECT id, {columns} FROM customers"
    )
    count = int(conn.exec_driver_sql(f"SELECT count(*) FROM {SEARCH_TABLE}").scalar() or 0)
    return SearchIndexStatus(enabled=True, indexed_rows=count)


def ensure_index(engine: Engine) -> SearchIndexStatus:
    """Initialize or repair the index without rebuilding a healthy projection."""
    with engine.begin() as conn:
        if conn.dialect.name != "sqlite" or not _fts5_supported(conn):
            return SearchIndexStatus(enabled=False, indexed_rows=0)
        _create_schema(conn)
        source_count = int(conn.exec_driver_sql("SELECT count(*) FROM customers").scalar() or 0)
        indexed_count = int(
            conn.exec_driver_sql(f"SELECT count(*) FROM {SEARCH_TABLE}").scalar() or 0
        )
        if source_count != indexed_count:
            return rebuild_index(conn)
        return SearchIndexStatus(enabled=True, indexed_rows=indexed_count)


_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def build_match_expression(query: str) -> str | None:
    """Convert untrusted text into a quoted, prefix-matching FTS expression."""
    tokens = _TOKEN_RE.findall(query.casefold())
    if not tokens:
        return None
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"*' for token in tokens)


def search_customers(
    db: Session,
    *,
    query: str,
    page: int,
    page_size: int,
) -> CustomerPage:
    """Search the projection and return base-table rows in weighted BM25 order."""
    match = build_match_expression(query)
    if match is None:
        return CustomerPage(
            meta=PageMeta(total=0, page=page, page_size=page_size, pages=0), items=[]
        )

    try:
        total = int(
            db.execute(
                text(f"SELECT count(*) FROM {SEARCH_TABLE} WHERE {SEARCH_TABLE} MATCH :query"),
                {"query": match},
            ).scalar()
            or 0
        )
        # Name/code and category-style text receive higher weights than the
        # numeric facets.  rowid is a deterministic tie-breaker.
        ids = list(
            db.execute(
                text(
                    f"SELECT rowid FROM {SEARCH_TABLE} "
                    f"WHERE {SEARCH_TABLE} MATCH :query "
                    f"ORDER BY bm25({SEARCH_TABLE}, 8.0, 4.0, 1.0, 1.0, 1.0), rowid "
                    "LIMIT :limit OFFSET :offset"
                ),
                {"query": match, "limit": page_size, "offset": (page - 1) * page_size},
            ).scalars()
        )
    except Exception as exc:  # missing/corrupt projection or unsupported FTS5
        raise SearchIndexUnavailable from exc

    customers = {
        item.id: item
        for item in db.scalars(select(Customer).where(Customer.id.in_(ids))).all()
    }
    pages = math.ceil(total / page_size) if total else 0
    return CustomerPage(
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
        items=[
            CustomerOut.model_validate(customers[row_id])
            for row_id in ids
            if row_id in customers
        ],
    )
