"""Automated API tests for the Shopping API.

Run with ``pytest`` from the ``shopping-api`` directory.
"""
from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_default_pagination(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 200
    assert body["meta"]["limit"] == 20
    assert body["meta"]["count"] == 20
    assert len(body["items"]) == 20
    # Default sort is by customer_id ascending.
    assert body["items"][0]["customer_id"] == "0001"


def test_pagination_offset(client):
    resp = client.get("/customers", params={"limit": 5, "offset": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["limit"] == 5
    assert body["meta"]["offset"] == 5
    assert [c["customer_id"] for c in body["items"]] == [
        "0006",
        "0007",
        "0008",
        "0009",
        "0010",
    ]


def test_filter_by_gender(client):
    resp = client.get("/customers", params={"gender": "Female", "limit": 100})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 112  # 112 Female customers in the dataset
    assert all(c["gender"] == "Female" for c in body["items"])


def test_filter_age_range(client):
    resp = client.get("/customers", params={"min_age": 30, "max_age": 35, "limit": 100})
    assert resp.status_code == 200
    body = resp.json()
    assert all(30 <= c["age"] <= 35 for c in body["items"])
    assert body["meta"]["total"] == body["meta"]["count"]


def test_filter_income_and_spending(client):
    resp = client.get(
        "/customers",
        params={"min_income": 70, "max_income": 80, "min_spending": 80, "limit": 100},
    )
    assert resp.status_code == 200
    for c in resp.json()["items"]:
        assert 70 <= c["annual_income"] <= 80
        assert c["spending_score"] >= 80


def test_search_by_customer_id(client):
    resp = client.get("/customers", params={"search": "0199"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["customer_id"] == "0199"


def test_sorting_desc(client):
    resp = client.get(
        "/customers", params={"sort_by": "annual_income", "order": "desc", "limit": 1}
    )
    assert resp.status_code == 200
    assert resp.json()["items"][0]["annual_income"] == 137


def test_get_single_customer(client):
    resp = client.get("/customers/0001")
    assert resp.status_code == 200
    assert resp.json() == {
        "customer_id": "0001",
        "gender": "Male",
        "age": 19,
        "annual_income": 15,
        "spending_score": 39,
    }


def test_get_missing_customer_returns_404(client):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_invalid_age_range_returns_422(client):
    resp = client.get("/customers", params={"min_age": 50, "max_age": 20})
    assert resp.status_code == 422


def test_invalid_gender_returns_422(client):
    resp = client.get("/customers", params={"gender": "Other"})
    assert resp.status_code == 422


def test_limit_over_max_returns_422(client):
    resp = client.get("/customers", params={"limit": 1000})
    assert resp.status_code == 422


def test_stats(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_customers"] == 200
    assert body["gender_breakdown"] == {"Female": 112, "Male": 88}
    assert body["age"]["min"] == 18
    assert body["age"]["max"] == 70
    assert body["annual_income"]["max"] == 137
    assert 1 <= body["spending_score"]["min"] <= body["spending_score"]["max"] <= 100
