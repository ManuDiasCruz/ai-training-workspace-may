from __future__ import annotations

import math
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schemas import CustomerOut, CustomerPage, PageMeta

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _is_sqlite(db: Session) -> bool:
    return db.get_bind().dialect.name == "sqlite"


def ensure_customer_search_index(db: Session) -> None:
    if not _is_sqlite(db):
        return

    db.execute(
        text(
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
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS customers_ai AFTER INSERT ON customers BEGIN
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
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS customers_ad AFTER DELETE ON customers BEGIN
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
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS customers_au AFTER UPDATE ON customers BEGIN
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
            """
        )
    )
    rebuild_customer_search_index(db)


def rebuild_customer_search_index(db: Session) -> None:
    if _is_sqlite(db):
        db.execute(text("INSERT INTO customers_fts(customers_fts) VALUES ('rebuild')"))


def build_fts_query(raw_query: str) -> str:
    tokens = TOKEN_RE.findall(raw_query.lower())
    if not tokens:
        raise ValueError("Search query must include at least one letter or number")
    return " OR ".join(f"{token}*" for token in tokens)


def search_customers(db: Session, raw_query: str, *, page: int, page_size: int) -> CustomerPage:
    fts_query = build_fts_query(raw_query)
    offset = (page - 1) * page_size
    total = (
        db.execute(
            text("SELECT count(*) FROM customers_fts WHERE customers_fts MATCH :query"),
            {"query": fts_query},
        ).scalar_one()
        or 0
    )
    rows = db.execute(
        text(
            """
            SELECT
                c.id,
                c.customer_id,
                c.genre,
                c.age,
                c.annual_income_k,
                c.spending_score
            FROM customers_fts
            JOIN customers AS c ON c.id = customers_fts.rowid
            WHERE customers_fts MATCH :query
            ORDER BY bm25(customers_fts), c.id
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
