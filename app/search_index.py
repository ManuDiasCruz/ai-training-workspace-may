from __future__ import annotations

from sqlalchemy.engine import Engine


SEARCH_TABLE = "customer_search"
SEARCH_COLUMNS = (
    "customer_id",
    "genre",
    "age",
    "annual_income_k",
    "spending_score",
)


def ensure_customer_search_index(engine: Engine) -> None:
    """Create and refresh the SQLite FTS5 index used by /search."""

    if engine.dialect.name != "sqlite":
        return

    columns = ", ".join(SEARCH_COLUMNS)
    new_values = ", ".join(f"new.{column}" for column in SEARCH_COLUMNS)
    old_values = ", ".join(f"old.{column}" for column in SEARCH_COLUMNS)

    with engine.begin() as conn:
        conn.exec_driver_sql(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {SEARCH_TABLE}
            USING fts5(
                {columns},
                content='customers',
                content_rowid='id'
            )
            """
        )
        conn.exec_driver_sql(
            f"""
            CREATE TRIGGER IF NOT EXISTS customers_search_ai
            AFTER INSERT ON customers BEGIN
                INSERT INTO {SEARCH_TABLE}(rowid, {columns})
                VALUES (new.id, {new_values});
            END
            """
        )
        conn.exec_driver_sql(
            f"""
            CREATE TRIGGER IF NOT EXISTS customers_search_ad
            AFTER DELETE ON customers BEGIN
                INSERT INTO {SEARCH_TABLE}({SEARCH_TABLE}, rowid, {columns})
                VALUES ('delete', old.id, {old_values});
            END
            """
        )
        conn.exec_driver_sql(
            f"""
            CREATE TRIGGER IF NOT EXISTS customers_search_au
            AFTER UPDATE ON customers BEGIN
                INSERT INTO {SEARCH_TABLE}({SEARCH_TABLE}, rowid, {columns})
                VALUES ('delete', old.id, {old_values});
                INSERT INTO {SEARCH_TABLE}(rowid, {columns})
                VALUES (new.id, {new_values});
            END
            """
        )
        conn.exec_driver_sql(f"INSERT INTO {SEARCH_TABLE}({SEARCH_TABLE}) VALUES ('rebuild')")
