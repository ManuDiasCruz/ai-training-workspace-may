"""SQLite FTS5 full-text search index for the ``customers`` table.

Implements issue #6 ("Replace ILIKE search with SQLite FTS5"). The issue's
"Next Steps" describe a ``purchases`` table with ``item_purchased`` /
``category`` / ``color`` / ``location`` columns, but this branch models the
Mall Customer Segmentation dataset as a single flat ``customers`` table
(``customer_id``, ``genre``, ``age``, ``annual_income_k``,
``spending_score``). The issue's *intent* -- replace the unranked
``column ILIKE '%q%'`` scan with a scalable, relevance-ranked full-text
index -- is therefore applied to the columns that actually exist here.

Design
------
* An **external-content** FTS5 virtual table (``customers_fts``) that mirrors
  the searchable columns via ``content='customers'`` / ``content_rowid='id'``,
  so the index is a thin shadow of the base table with no duplicated data.
* ``AFTER INSERT/UPDATE/DELETE`` **triggers** that keep the index in sync with
  the ``customers`` table.
* A ``rebuild`` **bootstrap** (see :func:`rebuild_search_index`) used by the
  importer and on app startup so freshly imported rows are always indexed.
* An optional trigram-tokenized table (``customers_fts_trgm``) powering the
  ``?fuzzy=true`` substring / typo-tolerant search.

Every helper degrades gracefully: if the running SQLite build lacks FTS5 (or
the trigram tokenizer), the affected feature is skipped and the API falls back
to the legacy ``LIKE`` search.
"""

from __future__ import annotations

import re

from sqlalchemy.engine import Connection

FTS_TABLE = "customers_fts"
FTS_TRGM_TABLE = "customers_fts_trgm"

# Columns mirrored into the index. ``customer_id`` and ``genre`` are the
# natural text columns; the numeric columns are indexed as text so the
# previous "match any field" behaviour keeps working -- now BM25-ranked
# instead of a raw substring scan.
INDEXED_COLUMNS: tuple[str, ...] = (
    "customer_id",
    "genre",
    "age",
    "annual_income_k",
    "spending_score",
)


def _probe(conn: Connection, ddl: str, name: str) -> bool:
    """Return ``True`` if ``ddl`` (a CREATE VIRTUAL TABLE) works on this build."""
    try:
        conn.exec_driver_sql(ddl)
    except Exception:  # noqa: BLE001 - any failure means the feature is unavailable
        return False
    conn.exec_driver_sql(f"DROP TABLE IF EXISTS {name}")
    return True


def fts5_available(conn: Connection) -> bool:
    return _probe(
        conn, "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)", "_fts5_probe"
    )


def trigram_available(conn: Connection) -> bool:
    return _probe(
        conn,
        "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_trgm_probe USING fts5(x, tokenize='trigram')",
        "_fts5_trgm_probe",
    )


def _create_table_and_triggers(conn: Connection, table: str, tokenize: str, suffix: str) -> None:
    cols = ", ".join(INDEXED_COLUMNS)
    conn.exec_driver_sql(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS {table} "
        f"USING fts5({cols}, content='customers', content_rowid='id', tokenize='{tokenize}')"
    )
    insert_cols = "rowid, " + cols
    new_vals = "new.id, " + ", ".join(f"new.{c}" for c in INDEXED_COLUMNS)
    old_vals = "old.id, " + ", ".join(f"old.{c}" for c in INDEXED_COLUMNS)
    # External-content tables are kept in sync with explicit trigger statements.
    conn.exec_driver_sql(
        f"CREATE TRIGGER IF NOT EXISTS customers_ai{suffix} AFTER INSERT ON customers BEGIN "
        f"INSERT INTO {table}({insert_cols}) VALUES ({new_vals}); END"
    )
    conn.exec_driver_sql(
        f"CREATE TRIGGER IF NOT EXISTS customers_ad{suffix} AFTER DELETE ON customers BEGIN "
        f"INSERT INTO {table}({table}, {insert_cols}) VALUES('delete', {old_vals}); END"
    )
    conn.exec_driver_sql(
        f"CREATE TRIGGER IF NOT EXISTS customers_au{suffix} AFTER UPDATE ON customers BEGIN "
        f"INSERT INTO {table}({table}, {insert_cols}) VALUES('delete', {old_vals}); "
        f"INSERT INTO {table}({insert_cols}) VALUES ({new_vals}); END"
    )


def create_search_index(conn: Connection) -> dict[str, bool]:
    """Create the FTS5 table(s) and sync triggers when supported. Idempotent."""
    caps = {"fts5": False, "trigram": False}
    if not fts5_available(conn):
        return caps
    caps["fts5"] = True
    _create_table_and_triggers(conn, FTS_TABLE, "unicode61", "")
    if trigram_available(conn):
        caps["trigram"] = True
        _create_table_and_triggers(conn, FTS_TRGM_TABLE, "trigram", "_trgm")
    return caps


def rebuild_search_index(conn: Connection) -> dict[str, bool]:
    """Ensure the index exists and repopulate it from ``customers``.

    Safe to call after a bulk import: the FTS5 ``'rebuild'`` command rebuilds an
    external-content index directly from the base table, so the index ends up
    correct regardless of whether the sync triggers were present during the
    import.
    """
    caps = create_search_index(conn)
    if caps["fts5"]:
        conn.exec_driver_sql(f"INSERT INTO {FTS_TABLE}({FTS_TABLE}) VALUES('rebuild')")
    if caps["trigram"]:
        conn.exec_driver_sql(f"INSERT INTO {FTS_TRGM_TABLE}({FTS_TRGM_TABLE}) VALUES('rebuild')")
    return caps


def detect_capabilities(conn: Connection) -> dict[str, bool]:
    """Report which FTS tables currently exist in the database."""
    rows = conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?)",
        (FTS_TABLE, FTS_TRGM_TABLE),
    ).fetchall()
    names = {r[0] for r in rows}
    return {"fts5": FTS_TABLE in names, "trigram": FTS_TRGM_TABLE in names}


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def build_match_query(q: str, *, fuzzy: bool = False) -> str | None:
    """Translate user input into a safe FTS5 ``MATCH`` expression.

    Standard mode tokenises the query and prefix-matches every token (implicit
    AND), approximating the old substring behaviour while staying BM25-rankable.
    Fuzzy mode quotes the trimmed input as a single phrase for the trigram
    tokenizer (substring / typo tolerant); the trigram tokenizer needs at least
    three characters, so shorter fuzzy queries return ``None`` and the caller
    falls back to standard matching.

    Returns ``None`` when there is nothing to match. Every token is wrapped in
    double quotes (with embedded quotes doubled) so that FTS5 operators in user
    input can never alter the query structure -- the user query is treated as
    data, not as an FTS5 expression.
    """
    if fuzzy:
        s = q.strip()
        if len(s) < 3:
            return None
        return '"' + s.replace('"', '""') + '"'
    tokens = _TOKEN_RE.findall(q)
    if not tokens:
        return None
    return " ".join(f'"{t}"*' for t in tokens)
