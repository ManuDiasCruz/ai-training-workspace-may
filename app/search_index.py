"""SQLite FTS5 bootstrap and query helpers for customer search."""

from __future__ import annotations

import re

from sqlalchemy import Engine

_INDEX_STATEMENTS = (
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS customers_search USING fts5(
        customer_id,
        genre,
        age,
        annual_income_k,
        spending_score,
        content='customers',
        content_rowid='id'
    )
    """,
    """
    CREATE TRIGGER IF NOT EXISTS customers_search_ai AFTER INSERT ON customers BEGIN
        INSERT INTO customers_search(
            rowid, customer_id, genre, age, annual_income_k, spending_score
        ) VALUES (
            new.id, new.customer_id, new.genre, new.age,
            new.annual_income_k, new.spending_score
        );
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS customers_search_ad AFTER DELETE ON customers BEGIN
        INSERT INTO customers_search(
            customers_search, rowid, customer_id, genre, age,
            annual_income_k, spending_score
        ) VALUES (
            'delete', old.id, old.customer_id, old.genre, old.age,
            old.annual_income_k, old.spending_score
        );
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS customers_search_au AFTER UPDATE ON customers BEGIN
        INSERT INTO customers_search(
            customers_search, rowid, customer_id, genre, age,
            annual_income_k, spending_score
        ) VALUES (
            'delete', old.id, old.customer_id, old.genre, old.age,
            old.annual_income_k, old.spending_score
        );
        INSERT INTO customers_search(
            rowid, customer_id, genre, age, annual_income_k, spending_score
        ) VALUES (
            new.id, new.customer_id, new.genre, new.age,
            new.annual_income_k, new.spending_score
        );
    END
    """,
)


def ensure_search_index(engine: Engine, *, rebuild: bool = False) -> None:
    """Create the FTS table and sync triggers, optionally rebuilding existing rows."""
    with engine.begin() as connection:
        for statement in _INDEX_STATEMENTS:
            connection.exec_driver_sql(statement)
        if rebuild:
            connection.exec_driver_sql(
                "INSERT INTO customers_search(customers_search) VALUES ('rebuild')"
            )


def search_match_query(value: str) -> str:
    """Compile plain user text into an OR-based, prefix-aware FTS5 expression."""
    tokens = re.findall(r"[a-zA-Z0-9]+", value)
    if not tokens:
        raise ValueError("Search query must include letters or digits")
    return " OR ".join(f'"{token}"*' for token in tokens)
