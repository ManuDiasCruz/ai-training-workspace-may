"""Tests for the SQLite FTS5 search index (issue #6).

Covers the MATCH-query builder, BM25 ranking order on a controlled dataset,
and the /search endpoint behaviour (standard BM25 search + trigram fuzzy
substring search) against the real imported dataset.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import search_index

pytestmark = pytest.mark.anyio


# --------------------------------------------------------------------------- #
# build_match_query (unit)                                                     #
# --------------------------------------------------------------------------- #


def test_build_match_query_standard_prefixes_tokens():
    assert search_index.build_match_query("Female") == '"Female"*'
    assert search_index.build_match_query("fe ma") == '"fe"* "ma"*'


def test_build_match_query_ignores_punctuation_and_empty():
    assert search_index.build_match_query("   ") is None
    assert search_index.build_match_query("!!!") is None


def test_build_match_query_fuzzy_phrase_and_min_length():
    # >= 3 chars -> a quoted phrase for the trigram tokenizer
    assert search_index.build_match_query("ale", fuzzy=True) == '"ale"'
    # < 3 chars -> None so the caller falls back to standard matching
    assert search_index.build_match_query("ab", fuzzy=True) is None


def test_build_match_query_neutralises_fts5_operators():
    # A query that contains FTS5 syntax must be treated as data, not operators.
    match = search_index.build_match_query('cat OR "drop"')
    assert match == '"cat"* "OR"* "drop"*'


# --------------------------------------------------------------------------- #
# BM25 ranking order (issue #6, step 5)                                        #
# --------------------------------------------------------------------------- #


@pytest.fixture()
def ranking_engine(tmp_path):
    """A fresh DB with rows engineered to have a known BM25 ranking."""
    from app.db import Base
    from app.models import Customer  # noqa: F401 - registers the table on Base

    engine = create_engine(f"sqlite:///{tmp_path / 'rank.db'}", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all(
            [
                # id=1: token "40" appears in age, income AND score -> most relevant
                Customer(customer_id="0001", genre="Female", age=40, annual_income_k=40, spending_score=40),
                # id=2: token "40" appears only in age -> less relevant
                Customer(customer_id="0002", genre="Female", age=40, annual_income_k=15, spending_score=81),
                # id=3: no "40" anywhere -> must not match
                Customer(customer_id="0003", genre="Male", age=25, annual_income_k=30, spending_score=20),
            ]
        )
        s.commit()
    with engine.begin() as conn:
        caps = search_index.rebuild_search_index(conn)
    assert caps["fts5"], "FTS5 must be available for this test"
    return engine


def test_bm25_ranking_order(ranking_engine):
    match = search_index.build_match_query("40")
    fts = search_index.FTS_TABLE
    with ranking_engine.connect() as conn:
        ids = [
            r[0]
            for r in conn.exec_driver_sql(
                f"SELECT c.id FROM {fts} JOIN customers c ON c.id = {fts}.rowid "
                f"WHERE {fts} MATCH ? ORDER BY bm25({fts}), c.id",
                (match,),
            ).fetchall()
        ]
    # Only ids 1 and 2 contain "40"; id 1 (3 column hits) ranks above id 2 (1 hit).
    assert ids == [1, 2]


# --------------------------------------------------------------------------- #
# /search endpoint (real imported dataset)                                     #
# --------------------------------------------------------------------------- #


async def test_search_matches_only_relevant_rows(client):
    r = await client.get("/search", params={"q": "Female", "page_size": 200})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] > 0
    assert all(it["genre"] == "Female" for it in body["items"])


async def test_search_unknown_token_returns_empty(client):
    r = await client.get("/search", params={"q": "Zzzzqx"})
    assert r.status_code == 200
    assert r.json()["meta"]["total"] == 0


async def test_fuzzy_finds_substring_that_standard_misses(client):
    # "ale" is a prefix of no token, so standard search finds nothing...
    standard = (await client.get("/search", params={"q": "ale"})).json()
    assert standard["meta"]["total"] == 0
    # ...but it is a substring of both "Male" and "Female", so fuzzy matches all.
    fuzzy = (await client.get("/search", params={"q": "ale", "fuzzy": "true"})).json()
    assert fuzzy["meta"]["total"] == 200
