"""End-to-end API tests covering health, listing, pagination, filtering,
search, sorting, single-record retrieval, validation and statistics."""
from __future__ import annotations

# Known facts about the bundled dataset (200 records).
TOTAL = 200
FEMALE = 112
MALE = 88

CUSTOMERS = "/api/v1/customers"
STATS = "/api/v1/stats"


# --- meta --------------------------------------------------------------------
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["customers_loaded"] == TOTAL


def test_root_lists_entrypoints(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["health"] == "/health"


def test_openapi_schema_exposes_routes(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert CUSTOMERS in resp.json()["paths"]


# --- listing & pagination ----------------------------------------------------
def test_list_default_pagination(client):
    resp = client.get(CUSTOMERS)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 20
    pagination = body["pagination"]
    assert pagination["page"] == 1
    assert pagination["page_size"] == 20
    assert pagination["total_items"] == TOTAL
    assert pagination["total_pages"] == 10
    assert pagination["has_next"] is True
    assert pagination["has_previous"] is False


def test_pagination_navigates_pages(client):
    resp = client.get(CUSTOMERS, params={"page": 2, "page_size": 5})
    body = resp.json()
    assert len(body["data"]) == 5
    # default sort is customer_id asc, so page 2 begins at id 6.
    assert body["data"][0]["customer_id"] == 6
    assert body["pagination"]["has_previous"] is True
    assert body["pagination"]["has_next"] is True


def test_pagination_last_page_has_no_next(client):
    resp = client.get(CUSTOMERS, params={"page": 10, "page_size": 20})
    pagination = resp.json()["pagination"]
    assert pagination["has_next"] is False
    assert pagination["has_previous"] is True


# --- filtering ---------------------------------------------------------------
def test_filter_by_gender(client):
    resp = client.get(CUSTOMERS, params={"gender": "Female", "page_size": 100})
    body = resp.json()
    assert body["pagination"]["total_items"] == FEMALE
    assert all(c["gender"] == "Female" for c in body["data"])


def test_filter_by_age_range(client):
    resp = client.get(CUSTOMERS, params={"min_age": 30, "max_age": 40, "page_size": 100})
    data = resp.json()["data"]
    assert data
    assert all(30 <= c["age"] <= 40 for c in data)


def test_filter_by_income_and_spending_score(client):
    resp = client.get(
        CUSTOMERS,
        params={
            "min_income": 50,
            "max_income": 80,
            "min_spending_score": 40,
            "max_spending_score": 60,
            "page_size": 100,
        },
    )
    data = resp.json()["data"]
    assert data
    for c in data:
        assert 50 <= c["annual_income_k"] <= 80
        assert 40 <= c["spending_score"] <= 60


# --- search ------------------------------------------------------------------
def test_search_numeric_matches_customer_id(client):
    resp = client.get(CUSTOMERS, params={"search": "42"})
    body = resp.json()
    assert body["pagination"]["total_items"] == 1
    assert body["data"][0]["customer_id"] == 42


def test_search_gender_keyword_is_case_insensitive(client):
    resp = client.get(CUSTOMERS, params={"search": "female", "page_size": 100})
    body = resp.json()
    assert body["pagination"]["total_items"] == FEMALE
    assert all(c["gender"] == "Female" for c in body["data"])


# --- sorting -----------------------------------------------------------------
def test_sorting_by_spending_score_desc(client):
    resp = client.get(
        CUSTOMERS, params={"sort_by": "spending_score", "order": "desc", "page_size": 5}
    )
    scores = [c["spending_score"] for c in resp.json()["data"]]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 99


# --- single record -----------------------------------------------------------
def test_get_customer_found(client):
    resp = client.get(f"{CUSTOMERS}/1")
    assert resp.status_code == 200
    assert resp.json() == {
        "customer_id": 1,
        "gender": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }


def test_get_customer_not_found_returns_404(client):
    resp = client.get(f"{CUSTOMERS}/99999")
    assert resp.status_code == 404
    assert resp.json()["error"]["status"] == 404


# --- validation & error handling --------------------------------------------
def test_invalid_gender_returns_422(client):
    resp = client.get(CUSTOMERS, params={"gender": "Unknown"})
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["status"] == 422
    assert error["details"]


def test_inverted_range_returns_422(client):
    resp = client.get(CUSTOMERS, params={"min_age": 50, "max_age": 20})
    assert resp.status_code == 422
    assert "max_age" in resp.json()["error"]["message"]


def test_invalid_page_returns_422(client):
    resp = client.get(CUSTOMERS, params={"page": 0})
    assert resp.status_code == 422


def test_page_size_above_limit_returns_422(client):
    resp = client.get(CUSTOMERS, params={"page_size": 1000})
    assert resp.status_code == 422


# --- statistics --------------------------------------------------------------
def test_stats_unfiltered(client):
    resp = client.get(STATS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_customers"] == TOTAL
    assert body["gender_distribution"] == {"Male": MALE, "Female": FEMALE}
    assert body["age"]["min"] == 18
    assert body["age"]["max"] == 70
    assert body["spending_score"]["max"] == 99


def test_stats_with_filter(client):
    resp = client.get(STATS, params={"gender": "Male"})
    body = resp.json()
    assert body["total_customers"] == MALE
    assert body["gender_distribution"]["Female"] == 0
    assert body["filters_applied"] == {"gender": "Male"}
