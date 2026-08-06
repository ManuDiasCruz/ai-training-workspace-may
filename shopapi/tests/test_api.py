"""API tests running against a temporary database built from the real CSV."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_customers_default_pagination(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 200
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["pages"] == 10
    assert len(body["items"]) == 20
    assert body["items"][0] == {
        "id": 1,
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }


def test_list_customers_pagination_offsets(client):
    resp = client.get("/customers", params={"page": 3, "page_size": 7})
    assert resp.status_code == 200
    body = resp.json()
    assert [c["id"] for c in body["items"]] == list(range(15, 22))
    assert body["pages"] == 29  # ceil(200 / 7)


def test_list_customers_filters(client):
    resp = client.get(
        "/customers",
        params={"genre": "Female", "min_income": 100, "max_score": 30},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] > 0
    for item in body["items"]:
        assert item["genre"] == "Female"
        assert item["annual_income_k"] >= 100
        assert item["spending_score"] <= 30


def test_list_customers_sorting(client):
    resp = client.get(
        "/customers",
        params={"sort_by": "spending_score", "order": "desc", "page_size": 5},
    )
    assert resp.status_code == 200
    scores = [c["spending_score"] for c in resp.json()["items"]]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 99


def test_list_customers_rejects_inverted_range(client):
    resp = client.get("/customers", params={"min_age": 60, "max_age": 20})
    assert resp.status_code == 422
    assert "min_age" in resp.json()["detail"]


def test_list_customers_rejects_invalid_genre(client):
    resp = client.get("/customers", params={"genre": "Robot"})
    assert resp.status_code == 422


def test_list_customers_rejects_oversized_page(client):
    resp = client.get("/customers", params={"page_size": 500})
    assert resp.status_code == 422


def test_get_customer_by_id(client):
    resp = client.get("/customers/42")
    assert resp.status_code == 200
    assert resp.json() == {
        "id": 42,
        "genre": "Male",
        "age": 24,
        "annual_income_k": 38,
        "spending_score": 92,
    }


def test_get_customer_not_found(client):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_search_by_customer_code(client):
    resp = client.get("/customers/search", params={"q": "0042"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == 42


def test_search_by_genre_is_case_insensitive(client):
    resp = client.get("/customers/search", params={"q": "FEMALE", "page_size": 100})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 112
    assert all(c["genre"] == "Female" for c in body["items"])


def test_search_requires_query(client):
    resp = client.get("/customers/search", params={"q": ""})
    assert resp.status_code == 422


def test_stats(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_customers"] == 200
    assert body["avg_age"] == 38.85
    assert set(body["by_genre"]) == {"Male", "Female"}
    assert body["by_genre"]["Female"]["count"] == 112
    assert body["by_genre"]["Male"]["count"] == 88
