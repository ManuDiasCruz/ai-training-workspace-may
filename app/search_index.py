"""SQLite FTS5 full-text search index for the ``customers`` table.

Implements issue #6 ("Replace ILIKE search with SQLite FTS5"). Because the
shopping-customer dataset on this branch is the flat ``customers`` table
(``customer_id``, ``genre``, ``age``, ``annual_income_k``,
``spending_score``) rather than a ``purchases`` table, the issue's intent is
applied to the columns that actually exist here:

* an **external-content** FTS5 virtual table (``customers_fts``) mirroring the
  searchable customer columns, with ``content='customers'`` /
  ``content_rowid='id'`` so the index stays a thin shadow of the base table;
* **triggers** that keep the index in sync on INSERT/UPDATE/DELETE;
* a ``rebuild`` bootstrap used by the importer and app startup so freshly
  imported data is always indexed;
* an optional ``trigram`` index (``customers_fts_trgm``) powering the
  ``?fuzzy=true`` substring/typo-tolerant search.

All helpers degrade gracefully: if the running SQLite build lacks FTS5 (or the
trigram tokenizer), the relevant feature is skipped and the API falls back to
the legacy ``LIKE`` search.
"""

from __future__ import annotations

import re

from sqlalchemy.engine import Connection

FTS_TABLE = "customers_fts"
FTS_TRGM_TABLE = "customers_fts_trgm"

# Columns mirrored into the FTS index. ``customer_id`` and ``genre`` are the
# natural text columns; the numeric columns are indexed as text so the
# previous "match any field" behaviour keeps working -- now ranked by BM25.
FTS_COLUMNS: tuple[str, ...] = (
    "customer_id",
    "genre",
    "age",
    "annual_income_k",
    "spending_score",
)


def _can_create(conn: Connection, ddl: str, probe: str) -> bool:
    try:
        conn.exec_driver_sql(ddl)
        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {probe}")
        return True
    except Exception:  # noqa: BLE001 - any failure means "unsupported"
        return False


def fts5_available(conn: Connection) -> bool:
    return _can_create(
        conn, "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)", "_fts5_probe"
    )


def trigram_available(conn: Connection) -> bool:
    return _can_create(
        conn,
        "CREATE VIRTUAL TABLE IF NOT EXISTS _trgm_probe USING fts5(x, tokenize='trigram')",
        "_trgm_probe",
    )


def _sync_triggers(fts: str, suffix: str) -> list[str]:
    cols = ", ".join(FTS_COLUMNS)
    insert_cols = "rowid, " + cols
    new_vals = "new.id, " + ", ".join(f"new.{c}" for c in FTS_COLUMNS)
    old_vals = "old.id, " + ", ".join(f"old.{c}" for c in FTS_COLUMNS)
    return [
        f"CREATE TRIGGER IF NOT EXISTS customers_ai{suffix} AFTER INSERT ON customers BEGIN "
        f"INSERT INTO {fts}({insert_cols}) VALUES ({new_vals}); END",
        f"CREATE TRIGGER IF NOT EXISTS customers_ad{suffix} AFTER DELETE ON customers BEGIN "
        f"INSERT INTO {fts}({fts}, {insert_cols}) VALUES('delete', {old_vals}); END",
        f"CREATE TRIGGER IF NOT EXISTS customers_au{suffix} AFTER UPDATE ON customers BEGIN "
        f"INSERT INTO {fts}({fts}, {insert_cols}) VALUES('delete', {old_vals}); "
        f"INSERT INTO {fts}({insert_cols}) VALUES ({new_vals}); END",
    ]


def _create_fts_table(conn: Connection, name: str, tokenize: str) -> None:
    cols = ", ".join(FTS_COLUMNS)
    conn.exec_driver_sql(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS {name} "
        f"USING fts5({cols}, content='customers', content_rowid='id', tokenize='{tokenize}')"
    )


def create_search_index(conn: Connection) -> dict[str, bool]:
    """Create the FTS5 table(s) and sync triggers if supported. Idempotent."""
    caps = {"fts5": False, "trigram": False}
    if not fts5_available(conn):
        return caps
    caps["fts5"] = True
    _create_fts_table(conn, FTS_TABLE, "unicode61")
    for stmt in _sync_triggers(FTS_TABLE, ""):
        conn.exec_driver_sql(stmt)

    if trigram_available(conn):
        caps["trigram"] = True
        _create_fts_table(conn, FTS_TRGM_TABLE, "trigram")
        for stmt in _sync_triggers(FTS_TRGM_TABLE, "_trgm"):
            conn.exec_driver_sql(stmt)
    return caps


def rebuild_search_index(conn: Connection) -> dict[str, bool]:
    """(Re)create the index and repopulate it from the ``customers`` table."""
    caps = create_search_index(conn)
    if caps["fts5"]:
        conn.exec_driver_sql(f"INSERT INTO {FTS_TABLE}({FTS_TABLE}) VALUES('rebuild')")
    if caps["trigram"]:
        conn.exec_driver_sql(f"INSERT INTO {FTS_TRGM_TABLE}({FTS_TRGM_TABLE}) VALUES('rebuild')")
    return caps


def detect_capabilities(conn: Connection) -> dict[str, bool]:
    """Report which FTS tables actually exist in this database."""
    rows = conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?)",
        (FTS_TABLE, FTS_TRGM_TABLE),
    ).fetchall()
    names = {r[0] for r in rows}
    return {"fts5": FTS_TABLE in names, "trigram": FTS_TRGM_TABLE in names}


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def build_match_query(q: str, *, fuzzy: bool = False) -> str | None:
    """Translate a user query into a safe FTS5 ``MATCH`` expression.

    Standard mode tokenises the query and prefix-matches each token (implicit
    AND), approximating substring search while staying ranking-friendly.
    Fuzzy mode treats the trimmed input as a single phrase for the trigram
    tokenizer (substring/typo tolerant); trigram needs >= 3 characters, so
    shorter fuzzy queries return ``None`` and the caller falls back.
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
