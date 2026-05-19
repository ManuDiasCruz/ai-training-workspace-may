from __future__ import annotations


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_default_pagination(client):
    r = client.get("/purchases")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 20
    assert body["meta"]["total"] > 0
    assert len(body["items"]) == 20


def test_list_pagination_second_page_differs(client):
    p1 = client.get("/purchases", params={"page": 1, "page_size": 5}).json()
    p2 = client.get("/purchases", params={"page": 2, "page_size": 5}).json()
    ids1 = [it["id"] for it in p1["items"]]
    ids2 = [it["id"] for it in p2["items"]]
    assert len(ids1) == 5 and len(ids2) == 5
    assert set(ids1).isdisjoint(set(ids2))


def test_filter_by_category(client):
    r = client.get("/purchases", params={"category": "Footwear", "page_size": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] > 0
    assert all(it["category"] == "Footwear" for it in body["items"])


def test_filter_amount_range_validation(client):
    r = client.get("/purchases", params={"min_amount": 100, "max_amount": 10})
    assert r.status_code == 400


def test_filter_rating_out_of_range_rejected(client):
    r = client.get("/purchases", params={"min_rating": 9})
    assert r.status_code == 422


def test_get_single_and_404(client):
    r = client.get("/purchases/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1

    r = client.get("/purchases/99999999")
    assert r.status_code == 404


def test_search_returns_matching_rows(client):
    r = client.get("/search", params={"q": "Sneakers"})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["total"] >= 1
    assert all(
        "sneakers" in (it["item_purchased"] + it["category"] + it["color"] + it["location"]).lower()
        for it in body["items"]
    )


def test_search_requires_q(client):
    r = client.get("/search")
    assert r.status_code == 422


def test_categories_endpoint(client):
    r = client.get("/categories")
    assert r.status_code == 200
    cats = r.json()
    assert isinstance(cats, list) and len(cats) >= 1
    assert cats == sorted(cats)


def test_stats_endpoint(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_purchases"] > 0
    assert body["total_revenue_usd"] > 0
    assert 0 <= body["avg_review_rating"] <= 5
    assert len(body["by_category"]) >= 1
