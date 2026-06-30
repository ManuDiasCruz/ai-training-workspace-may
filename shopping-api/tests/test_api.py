"""Automated API tests covering listing, pagination, filtering, search,
validation and error handling."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_default_pagination(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 200          # full dataset size
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["count"] == 20
    assert len(body["items"]) == 20
    # Default sort is by customer_id ascending.
    assert body["items"][0]["customer_id"] == "0001"


def test_pagination_offset(client):
    page1 = client.get("/customers", params={"limit": 5, "offset": 0}).json()
    page2 = client.get("/customers", params={"limit": 5, "offset": 5}).json()
    assert [c["customer_id"] for c in page1["items"]] == [
        "0001", "0002", "0003", "0004", "0005",
    ]
    assert [c["customer_id"] for c in page2["items"]] == [
        "0006", "0007", "0008", "0009", "0010",
    ]


def test_filter_by_genre(client):
    resp = client.get("/customers", params={"genre": "Female", "limit": 100})
    body = resp.json()
    assert body["total"] == 112  # known count of Female records in dataset
    assert all(c["genre"] == "Female" for c in body["items"])


def test_filter_by_age_and_income_range(client):
    resp = client.get(
        "/customers",
        params={"min_age": 30, "max_age": 40, "min_income": 50, "max_income": 70, "limit": 100},
    )
    body = resp.json()
    assert body["total"] >= 1
    for c in body["items"]:
        assert 30 <= c["age"] <= 40
        assert 50 <= c["annual_income"] <= 70


def test_sorting(client):
    resp = client.get(
        "/customers", params={"sort_by": "spending_score", "order": "desc", "limit": 3}
    )
    scores = [c["spending_score"] for c in resp.json()["items"]]
    assert scores == sorted(scores, reverse=True)


def test_search_matches_numeric_value(client):
    # Search for income "137" -> two customers (0199, 0200) in the dataset.
    resp = client.get("/customers", params={"search": "137", "limit": 100})
    ids = {c["customer_id"] for c in resp.json()["items"]}
    assert {"0199", "0200"}.issubset(ids)


def test_get_single_customer(client):
    resp = client.get("/customers/0001")
    assert resp.status_code == 200
    assert resp.json() == {
        "customer_id": "0001",
        "genre": "Male",
        "age": 19,
        "annual_income": 15,
        "spending_score": 39,
    }


def test_get_missing_customer_returns_404(client):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_invalid_genre_is_rejected(client):
    resp = client.get("/customers", params={"genre": "Other"})
    assert resp.status_code == 422


def test_inverted_range_is_rejected(client):
    resp = client.get("/customers", params={"min_age": 50, "max_age": 20})
    assert resp.status_code == 422
    assert "min_age" in resp.json()["detail"]


def test_limit_upper_bound_enforced(client):
    resp = client.get("/customers", params={"limit": 1000})
    assert resp.status_code == 422


def test_stats_endpoint(client):
    resp = client.get("/customers/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 200
    assert 0 < body["avg_spending_score"] <= 100
    assert set(body["genre_breakdown"]) == {"Male", "Female"}
    assert sum(body["genre_breakdown"].values()) == 200
