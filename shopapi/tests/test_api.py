"""API tests for ShopAPI, run against a temporary seeded database."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["customers"] == 200


def test_list_customers_default_pagination(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 200
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["pages"] == 10
    assert len(body["items"]) == 20
    assert body["items"][0]["customer_id"] == 1


def test_list_customers_second_page(client):
    resp = client.get("/customers", params={"page": 2, "page_size": 50})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 50
    assert body["items"][0]["customer_id"] == 51
    assert body["pages"] == 4


def test_filter_by_genre_and_income(client):
    resp = client.get(
        "/customers",
        params={"genre": "Female", "min_income": 100, "page_size": 100},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] > 0
    for item in body["items"]:
        assert item["genre"] == "Female"
        assert item["annual_income_k"] >= 100


def test_filter_age_range_with_sorting(client):
    resp = client.get(
        "/customers",
        params={
            "min_age": 30,
            "max_age": 40,
            "sort_by": "spending_score",
            "order": "desc",
            "page_size": 100,
        },
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "expected at least one customer aged 30-40"
    scores = [item["spending_score"] for item in items]
    assert scores == sorted(scores, reverse=True)
    for item in items:
        assert 30 <= item["age"] <= 40


def test_get_customer_by_id(client):
    resp = client.get("/customers/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "customer_id": 1,
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }


def test_get_customer_not_found(client):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_search_by_id(client):
    resp = client.get("/customers/search", params={"q": "42"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["customer_id"] == 42


def test_search_by_genre_text(client):
    resp = client.get("/customers/search", params={"q": "fem", "page_size": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 112  # females in the dataset
    assert all(item["genre"] == "Female" for item in body["items"])


def test_validation_rejects_bad_page_size(client):
    resp = client.get("/customers", params={"page_size": 0})
    assert resp.status_code == 422


def test_validation_rejects_inverted_range(client):
    resp = client.get("/customers", params={"min_age": 50, "max_age": 20})
    assert resp.status_code == 400
    assert "min_age" in resp.json()["detail"]


def test_validation_rejects_unknown_genre(client):
    resp = client.get("/customers", params={"genre": "Other"})
    assert resp.status_code == 422


def test_stats_summary(client):
    resp = client.get("/stats/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_customers"] == 200
    assert body["by_genre"]["Female"]["count"] == 112
    assert body["by_genre"]["Male"]["count"] == 88
    assert body["min_annual_income_k"] == 15
    assert body["max_annual_income_k"] == 137
