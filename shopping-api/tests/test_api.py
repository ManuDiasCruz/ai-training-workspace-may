"""Automated API tests exercising listing, pagination, filtering, search,
single-record lookup, stats and input validation."""
from __future__ import annotations

TOTAL_RECORDS = 200


# --- meta -----------------------------------------------------------------

def test_health_reports_loaded_records(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["records"] == TOTAL_RECORDS


def test_root_lists_endpoints(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "/customers" in resp.json()["endpoints"]


# --- listing & pagination -------------------------------------------------

def test_list_default_pagination(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == TOTAL_RECORDS
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 20
    assert body["meta"]["total_pages"] == 10
    assert len(body["items"]) == 20
    # Response shape of a record.
    first = body["items"][0]
    assert set(first) == {"customer_id", "gender", "age", "annual_income_k", "spending_score"}


def test_pagination_returns_distinct_pages(client):
    page1 = client.get("/customers", params={"page": 1, "page_size": 5}).json()
    page2 = client.get("/customers", params={"page": 2, "page_size": 5}).json()
    ids1 = {c["customer_id"] for c in page1["items"]}
    ids2 = {c["customer_id"] for c in page2["items"]}
    assert len(ids1) == 5 and len(ids2) == 5
    assert ids1.isdisjoint(ids2)


def test_pagination_past_end_is_empty(client):
    resp = client.get("/customers", params={"page": 999, "page_size": 20})
    assert resp.status_code == 200
    assert resp.json()["items"] == []


# --- filtering ------------------------------------------------------------

def test_filter_by_gender(client):
    resp = client.get("/customers", params={"gender": "Male", "page_size": 100})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] > 0
    assert all(c["gender"] == "Male" for c in body["items"])


def test_filter_by_age_range(client):
    resp = client.get("/customers", params={"min_age": 30, "max_age": 40, "page_size": 100})
    assert resp.status_code == 200
    assert all(30 <= c["age"] <= 40 for c in resp.json()["items"])


def test_filter_combined_income_and_score(client):
    resp = client.get(
        "/customers",
        params={"min_income": 50, "max_income": 80, "min_spending_score": 40, "page_size": 100},
    )
    assert resp.status_code == 200
    for c in resp.json()["items"]:
        assert 50 <= c["annual_income_k"] <= 80
        assert c["spending_score"] >= 40


# --- search ---------------------------------------------------------------

def test_search_by_customer_id(client):
    resp = client.get("/customers", params={"search": "0007"})
    assert resp.status_code == 200
    ids = [c["customer_id"] for c in resp.json()["items"]]
    assert "0007" in ids


# --- sorting --------------------------------------------------------------

def test_sort_by_age_desc(client):
    resp = client.get("/customers", params={"sort_by": "age", "order": "desc", "page_size": 100})
    ages = [c["age"] for c in resp.json()["items"]]
    assert ages == sorted(ages, reverse=True)


# --- single record --------------------------------------------------------

def test_get_customer_found(client):
    resp = client.get("/customers/0001")
    assert resp.status_code == 200
    assert resp.json()["customer_id"] == "0001"


def test_get_customer_not_found(client):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# --- stats ----------------------------------------------------------------

def test_stats(client):
    body = client.get("/stats").json()
    assert body["total_customers"] == TOTAL_RECORDS
    assert sum(g["count"] for g in body["by_gender"]) == TOTAL_RECORDS
    assert body["age"]["min"] is not None and body["age"]["avg"] is not None


# --- validation & error handling ------------------------------------------

def test_page_size_over_limit_is_422(client):
    resp = client.get("/customers", params={"page_size": 500})
    assert resp.status_code == 422


def test_page_zero_is_422(client):
    resp = client.get("/customers", params={"page": 0})
    assert resp.status_code == 422


def test_min_age_greater_than_max_age_is_400(client):
    resp = client.get("/customers", params={"min_age": 60, "max_age": 20})
    assert resp.status_code == 400
    assert "cannot be greater than" in resp.json()["detail"]


def test_invalid_gender_enum_is_422(client):
    resp = client.get("/customers", params={"gender": "Other"})
    assert resp.status_code == 422
