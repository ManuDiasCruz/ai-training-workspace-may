from __future__ import annotations

import math
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schemas import CustomerOut, CustomerPage, PageMeta

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

# SQLite's trigram tokenizer only indexes terms of three or more characters,
# so fuzzy/substring queries shorter than this can never match.
TRIGRAM_MIN_TOKEN_LEN = 3

_FTS_COLUMNS = ("customer_id", "genre", "age", "annual_income_k", "spending_score")


def _is_sqlite(db: Session) -> bool:
    return db.get_bind().dialect.name == "sqlite"


def _create_fts_objects(db: Session, table: str, *, tokenize: str | None) -> None:
    columns = ",\n                ".join(_FTS_COLUMNS)
    insert_columns = ",\n                    ".join(_FTS_COLUMNS)
    new_values = ",\n                    ".join(f"new.{c}" for c in _FTS_COLUMNS)
    old_values = ",\n                    ".join(f"old.{c}" for c in _FTS_COLUMNS)
    tokenize_clause = f",\n                tokenize='{tokenize}'" if tokenize else ""

    db.execute(
        text(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING fts5(
                {columns},
                content='customers',
                content_rowid='id'{tokenize_clause}
            )
            """
        )
    )
    db.execute(
        text(
            f"""
            CREATE TRIGGER IF NOT EXISTS {table}_ai AFTER INSERT ON customers BEGIN
                INSERT INTO {table}(
                    rowid,
                    {insert_columns}
                )
                VALUES (
                    new.id,
                    {new_values}
                );
            END
            """
        )
    )
    db.execute(
        text(
            f"""
            CREATE TRIGGER IF NOT EXISTS {table}_ad AFTER DELETE ON customers BEGIN
                INSERT INTO {table}(
                    {table},
                    rowid,
                    {insert_columns}
                )
                VALUES (
                    'delete',
                    old.id,
                    {old_values}
                );
            END
            """
        )
    )
    db.execute(
        text(
            f"""
            CREATE TRIGGER IF NOT EXISTS {table}_au AFTER UPDATE ON customers BEGIN
                INSERT INTO {table}(
                    {table},
                    rowid,
                    {insert_columns}
                )
                VALUES (
                    'delete',
                    old.id,
                    {old_values}
                );
                INSERT INTO {table}(
                    rowid,
                    {insert_columns}
                )
                VALUES (
                    new.id,
                    {new_values}
                );
            END
            """
        )
    )


def ensure_customer_search_index(db: Session) -> None:
    if not _is_sqlite(db):
        return

    # Default tokenizer: prefix-aware relevance search.
    _create_fts_objects(db, "customers_fts", tokenize=None)
    # Trigram tokenizer: substring / typo-tolerant matching for ?fuzzy=true.
    _create_fts_objects(db, "customers_fts_trigram", tokenize="trigram")
    rebuild_customer_search_index(db)


def rebuild_customer_search_index(db: Session) -> None:
    if not _is_sqlite(db):
        return
    db.execute(text("INSERT INTO customers_fts(customers_fts) VALUES ('rebuild')"))
    db.execute(text("INSERT INTO customers_fts_trigram(customers_fts_trigram) VALUES ('rebuild')"))


def build_fts_query(raw_query: str) -> str:
    tokens = TOKEN_RE.findall(raw_query.lower())
    if not tokens:
        raise ValueError("Search query must include at least one letter or number")
    return " OR ".join(f"{token}*" for token in tokens)


def build_trigram_query(raw_query: str) -> str:
    tokens = [t for t in TOKEN_RE.findall(raw_query.lower()) if len(t) >= TRIGRAM_MIN_TOKEN_LEN]
    if not tokens:
        raise ValueError(
            f"Fuzzy search requires a term of at least {TRIGRAM_MIN_TOKEN_LEN} characters"
        )
    # Quoting each token as a string literal makes the trigram tokenizer treat
    # it as a single substring to look for rather than a boolean expression.
    return " OR ".join(f'"{token}"' for token in tokens)


def search_customers(
    db: Session,
    raw_query: str,
    *,
    page: int,
    page_size: int,
    fuzzy: bool = False,
) -> CustomerPage:
    if fuzzy:
        table = "customers_fts_trigram"
        fts_query = build_trigram_query(raw_query)
    else:
        table = "customers_fts"
        fts_query = build_fts_query(raw_query)

    offset = (page - 1) * page_size
    total = (
        db.execute(
            text(f"SELECT count(*) FROM {table} WHERE {table} MATCH :query"),
            {"query": fts_query},
        ).scalar_one()
        or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT
                c.id,
                c.customer_id,
                c.genre,
                c.age,
                c.annual_income_k,
                c.spending_score
            FROM {table}
            JOIN customers AS c ON c.id = {table}.rowid
            WHERE {table} MATCH :query
            ORDER BY bm25({table}), c.id
            LIMIT :limit OFFSET :offset
            """
        ),
        {"query": fts_query, "limit": page_size, "offset": offset},
    ).mappings()
    pages = math.ceil(total / page_size) if total else 0
    return CustomerPage(
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
        items=[CustomerOut.model_validate(dict(row)) for row in rows],
    )
