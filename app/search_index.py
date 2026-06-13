from __future__ import annotations

import re

from sqlalchemy import Engine, text

FTS_TABLE = "customers_fts"


def ensure_search_index(engine: Engine) -> None:
    """Create the FTS5 index and synchronization triggers when needed."""
    if engine.dialect.name != "sqlite":
        raise RuntimeError("The customer search index requires SQLite FTS5")

    with engine.begin() as connection:
        index_exists = connection.scalar(
            text(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = :table_name"
            ),
            {"table_name": FTS_TABLE},
        )
        connection.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS customers_fts USING fts5(
                    customer_id,
                    genre,
                    age,
                    annual_income_k,
                    spending_score,
                    content='customers',
                    content_rowid='id',
                    tokenize='unicode61'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS customers_fts_after_insert
                AFTER INSERT ON customers BEGIN
                    INSERT INTO customers_fts(
                        rowid, customer_id, genre, age, annual_income_k, spending_score
                    ) VALUES (
                        new.id,
                        new.customer_id,
                        new.genre,
                        new.age,
                        new.annual_income_k,
                        new.spending_score
                    );
                END
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS customers_fts_after_delete
                AFTER DELETE ON customers BEGIN
                    INSERT INTO customers_fts(
                        customers_fts,
                        rowid,
                        customer_id,
                        genre,
                        age,
                        annual_income_k,
                        spending_score
                    ) VALUES (
                        'delete',
                        old.id,
                        old.customer_id,
                        old.genre,
                        old.age,
                        old.annual_income_k,
                        old.spending_score
                    );
                END
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS customers_fts_after_update
                AFTER UPDATE ON customers BEGIN
                    INSERT INTO customers_fts(
                        customers_fts,
                        rowid,
                        customer_id,
                        genre,
                        age,
                        annual_income_k,
                        spending_score
                    ) VALUES (
                        'delete',
                        old.id,
                        old.customer_id,
                        old.genre,
                        old.age,
                        old.annual_income_k,
                        old.spending_score
                    );
                    INSERT INTO customers_fts(
                        rowid, customer_id, genre, age, annual_income_k, spending_score
                    ) VALUES (
                        new.id,
                        new.customer_id,
                        new.genre,
                        new.age,
                        new.annual_income_k,
                        new.spending_score
                    );
                END
                """
            )
        )
        if not index_exists:
            connection.execute(
                text("INSERT INTO customers_fts(customers_fts) VALUES ('rebuild')")
            )


def build_match_query(value: str) -> str | None:
    """Convert user input to a safe FTS5 prefix query."""
    tokens = re.findall(r"[^\W_]+", value, flags=re.UNICODE)
    if not tokens:
        return None
    return " AND ".join(f'"{token}"*' for token in tokens)
