from __future__ import annotations

import pytest
from sqlalchemy import delete

pytestmark = pytest.mark.anyio


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_list_default_pagination(client):
    r = await client.get("/customers")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"] == {"page": 1, "page_size": 20, "pages": 10, "total": 200}
    assert len(body["items"]) == 20
    assert body["items"][0]["customer_id"] == "0001"


async def test_list_pagination_second_page_differs(client):
    p1 = (await client.get("/customers", params={"page": 1, "page_size": 5})).json()
    p2 = (await client.get("/customers", params={"page": 2, "page_size": 5})).json()
    ids1 = [it["id"] for it in p1["items"]]
    ids2 = [it["id"] for it in p2["items"]]
    assert len(ids1) == 5 and len(ids2) == 5
    assert set(ids1).isdisjoint(set(ids2))


async def test_filter_by_genre_and_income_range(client):
    r = await client.get(
        "/customers",
        params={"genre": "Female", "min_annual_income_k": 70, "page_size": 100},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] > 0
    assert all(it["genre"] == "Female" and it["annual_income_k"] >= 70 for it in body["items"])


async def test_filter_range_validation(client):
    r = await client.get("/customers", params={"min_age": 60, "max_age": 30})
    assert r.status_code == 400
    assert r.json()["detail"] == "age minimum cannot exceed maximum"


async def test_filter_spending_score_out_of_range_rejected(client):
    r = await client.get("/customers", params={"min_spending_score": 101})
    assert r.status_code == 422


async def test_get_single_and_404(client):
    r = await client.get("/customers/0001")
    assert r.status_code == 200
    assert r.json()["customer_id"] == "0001"

    r = await client.get("/customers/9999")
    assert r.status_code == 404


async def test_search_returns_matching_rows(client):
    r = await client.get("/search", params={"q": "Female", "page_size": 25})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] >= 1
    assert all(
        "female"
        in (
            it["customer_id"]
            + it["genre"]
            + str(it["age"])
            + str(it["annual_income_k"])
            + str(it["spending_score"])
        ).lower()
        for it in body["items"]
    )


async def test_search_ranks_more_relevant_rows_first(client):
    from app.db import SessionLocal
    from app.models import Customer

    customer_ids = ["rank-alpha", "rank-alpha-alpha"]
    with SessionLocal() as session:
        session.add_all(
            [
                Customer(
                    customer_id="rank-alpha",
                    genre="Female",
                    age=30,
                    annual_income_k=70,
                    spending_score=50,
                ),
                Customer(
                    customer_id="rank-alpha-alpha",
                    genre="Female",
                    age=31,
                    annual_income_k=71,
                    spending_score=51,
                ),
            ]
        )
        session.commit()

    try:
        r = await client.get("/search", params={"q": "alpha", "page_size": 10})
        assert r.status_code == 200
        result_ids = [it["customer_id"] for it in r.json()["items"]]
        assert result_ids.index("rank-alpha-alpha") < result_ids.index("rank-alpha")
    finally:
        with SessionLocal() as session:
            session.execute(delete(Customer).where(Customer.customer_id.in_(customer_ids)))
            session.commit()


async def test_search_requires_q(client):
    r = await client.get("/search")
    assert r.status_code == 422


async def test_genres_endpoint(client):
    r = await client.get("/genres")
    assert r.status_code == 200
    assert r.json() == ["Female", "Male"]


async def test_stats_endpoint(client):
    r = await client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_customers"] == 200
    assert 18 <= body["avg_age"] <= 70
    assert body["min_annual_income_k"] == 15
    assert body["max_annual_income_k"] == 137
    assert len(body["by_genre"]) == 2
