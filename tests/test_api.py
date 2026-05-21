"""End-to-end tests over the shopping API."""

from __future__ import annotations


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_stats_returns_dataset_aggregates(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 200
    assert body["by_genre"] == {"Female": 112, "Male": 88}
    assert body["age"]["min"] == 18 and body["age"]["max"] == 70
    assert body["annual_income_k"]["max"] == 137
    assert 1 <= body["spending_score"]["min"] <= body["spending_score"]["max"] <= 100


def test_list_default_pagination(client):
    r = client.get("/customers")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"] == {"total": 200, "limit": 50, "offset": 0}
    assert len(body["items"]) == 50
    assert body["items"][0]["customer_id"] == 1


def test_list_pagination_offset(client):
    r = client.get("/customers", params={"limit": 10, "offset": 50})
    body = r.json()
    assert body["meta"]["offset"] == 50
    assert body["items"][0]["customer_id"] == 51
    assert len(body["items"]) == 10


def test_filter_by_genre_and_income(client):
    r = client.get(
        "/customers",
        params={"genre": "Female", "min_income": 100, "limit": 100},
    )
    body = r.json()
    assert body["meta"]["total"] >= 1
    assert all(item["genre"] == "Female" for item in body["items"])
    assert all(item["annual_income_k"] >= 100 for item in body["items"])


def test_filter_score_range(client):
    r = client.get("/customers", params={"min_score": 80, "max_score": 100, "limit": 500})
    body = r.json()
    assert all(80 <= item["spending_score"] <= 100 for item in body["items"])


def test_invalid_range_returns_400(client):
    r = client.get("/customers", params={"min_age": 60, "max_age": 20})
    assert r.status_code == 400


def test_search_by_genre_substring(client):
    r = client.get("/customers", params={"search": "Fem", "limit": 500})
    body = r.json()
    assert body["meta"]["total"] == 112
    assert all(item["genre"] == "Female" for item in body["items"])


def test_search_by_id_substring(client):
    r = client.get("/customers", params={"search": "199", "limit": 10})
    ids = {item["customer_id"] for item in r.json()["items"]}
    assert 199 in ids


def test_sort_by_income_desc(client):
    r = client.get(
        "/customers", params={"sort_by": "annual_income_k", "sort_order": "desc", "limit": 3}
    )
    incomes = [item["annual_income_k"] for item in r.json()["items"]]
    assert incomes == sorted(incomes, reverse=True)


def test_get_existing_customer(client):
    r = client.get("/customers/1")
    assert r.status_code == 200
    assert r.json() == {
        "customer_id": 1,
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }


def test_get_missing_customer_returns_404(client):
    r = client.get("/customers/99999")
    assert r.status_code == 404


def test_create_update_delete_flow(client):
    payload = {"genre": "Female", "age": 28, "annual_income_k": 75, "spending_score": 88}
    created = client.post("/customers", json=payload)
    assert created.status_code == 201
    new_id = created.json()["customer_id"]
    assert new_id == 201

    patched = client.patch(f"/customers/{new_id}", json={"spending_score": 99})
    assert patched.status_code == 200
    assert patched.json()["spending_score"] == 99

    deleted = client.delete(f"/customers/{new_id}")
    assert deleted.status_code == 204
    assert client.get(f"/customers/{new_id}").status_code == 404


def test_create_validation_rejects_bad_score(client):
    r = client.post(
        "/customers",
        json={"genre": "Male", "age": 30, "annual_income_k": 50, "spending_score": 150},
    )
    assert r.status_code == 422


def test_create_duplicate_id_conflict(client):
    payload = {
        "customer_id": 1,
        "genre": "Male",
        "age": 30,
        "annual_income_k": 50,
        "spending_score": 50,
    }
    r = client.post("/customers", json=payload)
    assert r.status_code == 409
