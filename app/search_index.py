from __future__ import annotations

import re

from sqlalchemy import Engine, text


SEARCH_COLUMNS = (
    "customer_id",
    "genre",
    "age",
    "annual_income_k",
    "spending_score",
)


def ensure_search_index(engine: Engine) -> None:
    """Create and backfill the SQLite FTS5 index used by /search."""
    if engine.dialect.name != "sqlite":
        return

    statements = [
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS customers_fts USING fts5(
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
        CREATE TRIGGER IF NOT EXISTS customers_fts_ai
        AFTER INSERT ON customers BEGIN
            INSERT INTO customers_fts(
                rowid,
                customer_id,
                genre,
                age,
                annual_income_k,
                spending_score
            )
            VALUES (
                new.id,
                new.customer_id,
                new.genre,
                new.age,
                new.annual_income_k,
                new.spending_score
            );
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS customers_fts_ad
        AFTER DELETE ON customers BEGIN
            INSERT INTO customers_fts(
                customers_fts,
                rowid,
                customer_id,
                genre,
                age,
                annual_income_k,
                spending_score
            )
            VALUES (
                'delete',
                old.id,
                old.customer_id,
                old.genre,
                old.age,
                old.annual_income_k,
                old.spending_score
            );
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS customers_fts_au
        AFTER UPDATE ON customers BEGIN
            INSERT INTO customers_fts(
                customers_fts,
                rowid,
                customer_id,
                genre,
                age,
                annual_income_k,
                spending_score
            )
            VALUES (
                'delete',
                old.id,
                old.customer_id,
                old.genre,
                old.age,
                old.annual_income_k,
                old.spending_score
            );
            INSERT INTO customers_fts(
                rowid,
                customer_id,
                genre,
                age,
                annual_income_k,
                spending_score
            )
            VALUES (
                new.id,
                new.customer_id,
                new.genre,
                new.age,
                new.annual_income_k,
                new.spending_score
            );
        END
        """,
        "INSERT INTO customers_fts(customers_fts) VALUES ('rebuild')",
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def build_fts_query(raw_query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", raw_query)
    return " OR ".join(f"{token}*" for token in tokens)
