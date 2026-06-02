"""Tests for the SQLite FTS5 search added in issue #6.

Covers BM25 relevance ranking, optional trigram (fuzzy) substring matching,
graceful handling of token-free queries, and the pure MATCH-query builders.
"""

from __future__ import annotations

import pytest

from app.search_index import build_match_query, build_trigram_query


# --- Pure query-builder unit tests (no DB/event loop needed) -----------------


def test_build_match_query_makes_anded_prefix_terms():
    # Case is preserved in the MATCH string; the unicode61 tokenizer folds case
    # at index/match time, so matching stays case-insensitive.
    assert build_match_query("Female") == '"Female"*'
    assert build_match_query("foo bar") == '"foo"* "bar"*'


def test_build_match_query_neutralises_fts_operators():
    # Embedded quotes/operators must be escaped, never interpreted as syntax.
    assert build_match_query('a" OR b') == '"a"* "OR"* "b"*'
    assert build_match_query("***") is None
    assert build_match_query("   ") is None


def test_build_trigram_query_requires_three_chars():
    assert build_trigram_query("emal") == '"emal"'
    assert build_trigram_query("ab") is None


# --- Endpoint behaviour ------------------------------------------------------


@pytest.mark.anyio
async def test_search_prefix_match_returns_genre(client):
    r = await client.get("/search", params={"q": "Female", "page_size": 200})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] >= 1
    assert all(it["genre"] == "Female" for it in body["items"])


@pytest.mark.anyio
async def test_search_ranks_by_bm25_relevance(client):
    """Rows matching the query term in more fields must rank earlier.

    With near-uniform document lengths and a single query term, BM25 ordering
    reduces to term-frequency: the more indexed fields a row matches, the
    better (lower) its score, so the match-count sequence must be
    non-increasing across the ranked page.
    """
    r = await client.get("/search", params={"q": "1", "page_size": 200})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) > 1

    def match_count(it: dict) -> int:
        fields = (it["age"], it["annual_income_k"], it["spending_score"])
        return sum(1 for v in fields if str(v).startswith("1"))

    counts = [match_count(it) for it in items]
    assert all(c >= 1 for c in counts)  # every result matched the term
    assert max(counts) > min(counts)  # the dataset gives a real ranking signal
    assert counts == sorted(counts, reverse=True)  # ranked best-match first


@pytest.mark.anyio
async def test_fuzzy_substring_matches_where_prefix_does_not(client):
    # "emal" is a substring of "Female" but not a prefix of any token.
    strict = (await client.get("/search", params={"q": "emal"})).json()
    assert strict["meta"]["total"] == 0

    fuzzy = (await client.get("/search", params={"q": "emal", "fuzzy": "true"})).json()
    assert fuzzy["meta"]["total"] >= 1
    assert all(it["genre"] == "Female" for it in fuzzy["items"])


@pytest.mark.anyio
async def test_search_pagination_is_disjoint_and_ranked(client):
    p1 = (await client.get("/search", params={"q": "1", "page": 1, "page_size": 5})).json()
    p2 = (await client.get("/search", params={"q": "1", "page": 2, "page_size": 5})).json()
    assert p1["meta"]["total"] == p2["meta"]["total"]
    ids1 = {it["id"] for it in p1["items"]}
    ids2 = {it["id"] for it in p2["items"]}
    assert len(ids1) == 5 and len(ids2) == 5
    assert ids1.isdisjoint(ids2)


@pytest.mark.anyio
async def test_search_token_free_query_returns_empty_page(client):
    r = await client.get("/search", params={"q": "!!!"})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] == 0
    assert body["items"] == []
