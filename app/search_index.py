"""SQLite FTS5 full-text search index for the shopping customer dataset.

Issue #6 asked us to replace the ``column ILIKE '%q%'`` based ``/search``
implementation with a real full-text index that provides relevance ranking
(BM25) and an optional typo/substring tolerant ``fuzzy`` mode.

The index is implemented as two FTS5 *external-content* virtual tables that
mirror the ``customers`` table (``content='customers'``, ``content_rowid='id'``)
so no data is duplicated beyond the inverted index itself:

* ``customers_fts`` — default ``unicode61`` tokenizer used for fast,
  BM25-ranked token/prefix matching. This is the primary search path.
* ``customers_fts_trigram`` — ``trigram`` tokenizer used for the optional
  ``?fuzzy=true`` substring search (the closest equivalent to the old
  ``ILIKE '%q%'`` behaviour, with typo tolerance).

A set of ``AFTER INSERT/UPDATE/DELETE`` triggers keeps both indexes in sync
with live writes to ``customers``. :func:`sync_search_index` performs a full
``'rebuild'`` and is called after a bulk CSV import so freshly imported data
is always indexed.

FTS5 is a SQLite-only feature, so every public helper degrades gracefully on
non-SQLite engines (e.g. a Postgres deployment profile): the index is simply
not created and callers fall back to the legacy ``ILIKE`` path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Columns mirrored into the FTS indexes, in a fixed order.
_FTS_COLUMNS = ("customer_id", "genre", "age", "annual_income_k", "spending_score")
_COLS = ", ".join(_FTS_COLUMNS)
_NEW_VALUES = ", ".join(f"new.{c}" for c in _FTS_COLUMNS)
_OLD_VALUES = ", ".join(f"old.{c}" for c in _FTS_COLUMNS)

# Trigram matching needs at least three characters to form a single trigram.
_MIN_TRIGRAM_LEN = 3

_CREATE_STATEMENTS = (
    f"""
    CREATE VIRTUAL TABLE IF NOT EXISTS customers_fts USING fts5(
        {_COLS},
        content='customers',
        content_rowid='id'
    )
    """,
    f"""
    CREATE VIRTUAL TABLE IF NOT EXISTS customers_fts_trigram USING fts5(
        {_COLS},
        content='customers',
        content_rowid='id',
        tokenize='trigram'
    )
    """,
    # Keep both indexes in sync with live writes to ``customers``.
    f"""
    CREATE TRIGGER IF NOT EXISTS customers_fts_ai AFTER INSERT ON customers BEGIN
        INSERT INTO customers_fts(rowid, {_COLS}) VALUES (new.id, {_NEW_VALUES});
        INSERT INTO customers_fts_trigram(rowid, {_COLS}) VALUES (new.id, {_NEW_VALUES});
    END
    """,
    f"""
    CREATE TRIGGER IF NOT EXISTS customers_fts_ad AFTER DELETE ON customers BEGIN
        INSERT INTO customers_fts(customers_fts, rowid, {_COLS})
            VALUES ('delete', old.id, {_OLD_VALUES});
        INSERT INTO customers_fts_trigram(customers_fts_trigram, rowid, {_COLS})
            VALUES ('delete', old.id, {_OLD_VALUES});
    END
    """,
    f"""
    CREATE TRIGGER IF NOT EXISTS customers_fts_au AFTER UPDATE ON customers BEGIN
        INSERT INTO customers_fts(customers_fts, rowid, {_COLS})
            VALUES ('delete', old.id, {_OLD_VALUES});
        INSERT INTO customers_fts(rowid, {_COLS}) VALUES (new.id, {_NEW_VALUES});
        INSERT INTO customers_fts_trigram(customers_fts_trigram, rowid, {_COLS})
            VALUES ('delete', old.id, {_OLD_VALUES});
        INSERT INTO customers_fts_trigram(rowid, {_COLS}) VALUES (new.id, {_NEW_VALUES});
    END
    """,
)


def is_sqlite(engine: Engine) -> bool:
    """Return True when the bound engine is SQLite (FTS5 is SQLite-only)."""
    return engine.dialect.name == "sqlite"


def ensure_search_index(engine: Engine) -> bool:
    """Create the FTS5 virtual tables and sync triggers if missing.

    Returns True when the index exists (or was created), False on non-SQLite
    engines where FTS5 is unavailable.
    """
    if not is_sqlite(engine):
        return False
    with engine.begin() as conn:
        for stmt in _CREATE_STATEMENTS:
            conn.execute(text(stmt))
    return True


def rebuild_search_index(engine: Engine) -> None:
    """Repopulate both FTS indexes from the ``customers`` content table."""
    if not is_sqlite(engine):
        return
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO customers_fts(customers_fts) VALUES('rebuild')"))
        conn.execute(
            text("INSERT INTO customers_fts_trigram(customers_fts_trigram) VALUES('rebuild')")
        )


def sync_search_index(engine: Engine) -> None:
    """Ensure the index exists and fully rebuild it (used after a CSV import)."""
    if ensure_search_index(engine):
        rebuild_search_index(engine)


def _quote(token: str) -> str:
    """Wrap a token as an FTS5 string literal (escaping embedded quotes)."""
    return '"' + token.replace('"', '""') + '"'


def build_match_query(q: str) -> str | None:
    """Build a BM25 prefix MATCH expression from free-text input.

    The input is split into alphanumeric tokens; each becomes a quoted prefix
    term (``"foo"*``) and the terms are AND-ed together (FTS5 default). Quoting
    neutralises FTS5 query operators so user input cannot inject syntax.

    Returns ``None`` when the query contains no usable tokens.
    """
    tokens = re.findall(r"[A-Za-z0-9]+", q)
    if not tokens:
        return None
    return " ".join(f"{_quote(token)}*" for token in tokens)


def build_trigram_query(q: str) -> str | None:
    """Build a substring MATCH expression for the trigram (fuzzy) index.

    Returns ``None`` when the trimmed query is shorter than a single trigram,
    in which case the caller should fall back to the prefix path.
    """
    cleaned = q.strip()
    if len(cleaned) < _MIN_TRIGRAM_LEN:
        return None
    return _quote(cleaned)


@dataclass
class SearchResult:
    total: int
    ids: list[int]


def search_ids(
    engine: Engine,
    q: str,
    *,
    fuzzy: bool,
    page: int,
    page_size: int,
) -> SearchResult | None:
    """Run a ranked FTS5 search and return matching customer ids by relevance.

    Returns ``None`` when FTS5 is unavailable (non-SQLite engine) so the caller
    can fall back to the legacy ``ILIKE`` search. Returns an empty
    :class:`SearchResult` when the query has no usable tokens.
    """
    if not is_sqlite(engine):
        return None

    table = "customers_fts"
    match = build_match_query(q)
    if fuzzy:
        trigram_match = build_trigram_query(q)
        if trigram_match is not None:
            table = "customers_fts_trigram"
            match = trigram_match
        # else: query too short for trigrams -> fall back to prefix match.

    if match is None:
        return SearchResult(total=0, ids=[])

    offset = (page - 1) * page_size
    with engine.connect() as conn:
        total = conn.execute(
            text(f"SELECT count(*) FROM {table} WHERE {table} MATCH :m"),
            {"m": match},
        ).scalar_one()
        rows = conn.execute(
            text(
                f"SELECT rowid FROM {table} WHERE {table} MATCH :m "
                f"ORDER BY bm25({table}), rowid LIMIT :limit OFFSET :offset"
            ),
            {"m": match, "limit": page_size, "offset": offset},
        ).all()
    return SearchResult(total=int(total or 0), ids=[int(r[0]) for r in rows])
