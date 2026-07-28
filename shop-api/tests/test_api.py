"""Automated API tests.

Covers the four required behaviours (listing, pagination, filtering, search)
plus validation, error handling and the aggregate endpoints.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config

TOTAL = 200
FEMALE_COUNT = 112
MALE_COUNT = 88
CUSTOMERS = f"{config.API_PREFIX}/customers"
STATS = f"{config.API_PREFIX}/stats"


# --------------------------------------------------------------------------
# meta
# --------------------------------------------------------------------------


def test_health_reports_loaded_dataset(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["record_count"] == TOTAL
    assert body["source_file"] == "Shopping_data.csv"
    assert body["imported_at"]


def test_openapi_schema_is_served(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert CUSTOMERS in response.json()["paths"]


# --------------------------------------------------------------------------
# listing
# --------------------------------------------------------------------------


def test_list_returns_first_page_with_meta(client: TestClient) -> None:
    response = client.get(CUSTOMERS)
    assert response.status_code == 200
    body = response.json()

    assert body["meta"] == {
        "page": 1,
        "page_size": config.DEFAULT_PAGE_SIZE,
        "total_items": TOTAL,
        "total_pages": TOTAL // config.DEFAULT_PAGE_SIZE,
        "has_next": True,
        "has_prev": False,
    }
    assert len(body["data"]) == config.DEFAULT_PAGE_SIZE


def test_record_shape_matches_source_row(client: TestClient) -> None:
    """The first CSV row is 0001,Male,19,15,39."""
    record = client.get(f"{CUSTOMERS}/0001").json()
    assert record == {
        "customer_id": "0001",
        "gender": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
        "segment": "frugal",
    }


# --------------------------------------------------------------------------
# pagination
# --------------------------------------------------------------------------


def test_pages_do_not_overlap(client: TestClient) -> None:
    first = client.get(CUSTOMERS, params={"page": 1, "page_size": 10}).json()
    second = client.get(CUSTOMERS, params={"page": 2, "page_size": 10}).json()
    first_ids = {row["customer_id"] for row in first["data"]}
    second_ids = {row["customer_id"] for row in second["data"]}
    assert first_ids.isdisjoint(second_ids)
    assert first["data"][0]["customer_id"] == "0001"
    assert second["data"][0]["customer_id"] == "0011"


def test_pagination_walks_every_record_exactly_once(client: TestClient) -> None:
    """Page through the whole dataset: no gaps, no duplicates."""
    seen: list[str] = []
    page = 1
    while True:
        body = client.get(CUSTOMERS, params={"page": page, "page_size": 30}).json()
        seen.extend(row["customer_id"] for row in body["data"])
        if not body["meta"]["has_next"]:
            break
        page += 1
    assert len(seen) == TOTAL
    assert len(set(seen)) == TOTAL
    assert seen == sorted(seen)


def test_last_page_is_partial_and_has_no_next(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"page": 7, "page_size": 30}).json()
    assert body["meta"]["total_pages"] == 7
    assert body["meta"]["has_next"] is False
    assert body["meta"]["has_prev"] is True
    assert len(body["data"]) == TOTAL - 6 * 30  # 20 remaining


def test_page_beyond_the_end_is_empty_not_an_error(client: TestClient) -> None:
    response = client.get(CUSTOMERS, params={"page": 999})
    assert response.status_code == 200
    assert response.json()["data"] == []


# --------------------------------------------------------------------------
# filtering
# --------------------------------------------------------------------------


def test_filter_by_gender(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"gender": "Female", "page_size": 100}).json()
    assert body["meta"]["total_items"] == FEMALE_COUNT
    assert {row["gender"] for row in body["data"]} == {"Female"}


def test_gender_filter_is_case_insensitive(client: TestClient) -> None:
    lowered = client.get(CUSTOMERS, params={"gender": "male"}).json()
    assert lowered["meta"]["total_items"] == MALE_COUNT


def test_filter_by_age_range(client: TestClient) -> None:
    body = client.get(
        CUSTOMERS, params={"age_min": 30, "age_max": 35, "page_size": 100}
    ).json()
    assert body["meta"]["total_items"] > 0
    assert all(30 <= row["age"] <= 35 for row in body["data"])


def test_filters_combine_with_and(client: TestClient) -> None:
    params = {
        "gender": "Male",
        "income_min": 70,
        "score_min": 60,
        "page_size": 100,
    }
    body = client.get(CUSTOMERS, params=params).json()
    assert body["meta"]["total_items"] > 0
    for row in body["data"]:
        assert row["gender"] == "Male"
        assert row["annual_income_k"] >= 70
        assert row["spending_score"] >= 60


def test_filter_by_segment(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"segment": "target", "page_size": 100}).json()
    assert body["meta"]["total_items"] == 38
    for row in body["data"]:
        assert row["segment"] == "target"
        assert row["annual_income_k"] >= 70
        assert row["spending_score"] >= 60


def test_filter_with_no_matches_returns_empty_page(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"age_min": 119, "age_max": 120}).json()
    assert body["meta"]["total_items"] == 0
    assert body["meta"]["total_pages"] == 0
    assert body["meta"]["has_prev"] is False
    assert body["data"] == []


# --------------------------------------------------------------------------
# search
# --------------------------------------------------------------------------


def test_search_matches_customer_id_substring(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"q": "0007"}).json()
    assert [row["customer_id"] for row in body["data"]] == ["0007"]


def test_search_matches_gender_label(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"q": "fem", "page_size": 100}).json()
    assert body["meta"]["total_items"] == FEMALE_COUNT


def test_search_treats_like_wildcards_literally(client: TestClient) -> None:
    """A bare '%' must not match every row."""
    body = client.get(CUSTOMERS, params={"q": "%"}).json()
    assert body["meta"]["total_items"] == 0


def test_search_combines_with_filters(client: TestClient) -> None:
    body = client.get(
        CUSTOMERS, params={"q": "male", "gender": "Female", "page_size": 100}
    ).json()
    # 'male' is a substring of 'Female', so the search matches every row and the
    # gender filter is what narrows the result.
    assert body["meta"]["total_items"] == FEMALE_COUNT


# --------------------------------------------------------------------------
# sorting
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sort_by", "order"),
    [
        ("age", "asc"),
        ("age", "desc"),
        ("annual_income_k", "desc"),
        ("spending_score", "asc"),
    ],
)
def test_sorting(client: TestClient, sort_by: str, order: str) -> None:
    body = client.get(
        CUSTOMERS, params={"sort_by": sort_by, "order": order, "page_size": 100}
    ).json()
    values = [row[sort_by] for row in body["data"]]
    assert values == sorted(values, reverse=order == "desc")


# --------------------------------------------------------------------------
# single record
# --------------------------------------------------------------------------


@pytest.mark.parametrize("requested", ["0042", "42"])
def test_lookup_accepts_padded_and_unpadded_ids(
    client: TestClient, requested: str
) -> None:
    response = client.get(f"{CUSTOMERS}/{requested}")
    assert response.status_code == 200
    assert response.json()["customer_id"] == "0042"


def test_unknown_id_returns_404_envelope(client: TestClient) -> None:
    response = client.get(f"{CUSTOMERS}/9999")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert "9999" in error["message"]


def test_non_numeric_id_is_rejected(client: TestClient) -> None:
    response = client.get(f"{CUSTOMERS}/not-an-id")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


# --------------------------------------------------------------------------
# validation and error handling
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": -1},
        {"page_size": 0},
        {"page_size": config.MAX_PAGE_SIZE + 1},
        {"gender": "Nonbinary"},
        {"segment": "vip"},
        {"age_min": -5},
        {"age_max": 200},
        {"score_min": 0},
        {"score_max": 101},
        {"sort_by": "id; DROP TABLE customers"},
        {"order": "sideways"},
    ],
)
def test_invalid_parameters_return_422(client: TestClient, params: dict) -> None:
    response = client.get(CUSTOMERS, params=params)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]


def test_unknown_query_parameter_is_rejected(client: TestClient) -> None:
    """A typo should fail loudly rather than be ignored as an unapplied filter."""
    response = client.get(CUSTOMERS, params={"genderr": "Male"})
    assert response.status_code == 422
    fields = [detail["field"] for detail in response.json()["error"]["details"]]
    assert "genderr" in fields


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"age_min": 50, "age_max": 20}, "age_max"),
        ({"income_min": 90, "income_max": 30}, "income_max"),
        ({"score_min": 80, "score_max": 10}, "score_max"),
    ],
)
def test_inverted_ranges_are_rejected(
    client: TestClient, params: dict, field: str
) -> None:
    response = client.get(CUSTOMERS, params=params)
    assert response.status_code == 422
    message = " ".join(
        detail["message"] for detail in response.json()["error"]["details"]
    )
    assert field in message


def test_sql_injection_attempt_does_not_execute(client: TestClient) -> None:
    """The payload must be treated as data; the table must survive."""
    response = client.get(CUSTOMERS, params={"q": "'; DROP TABLE customers; --"})
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 0
    assert client.get("/health").json()["record_count"] == TOTAL


def test_missing_database_returns_503_with_guidance(client: TestClient) -> None:
    previous = os.environ[config.DB_ENV_VAR]
    os.environ[config.DB_ENV_VAR] = str(Path(previous).parent / "absent.db")
    try:
        response = client.get(CUSTOMERS)
    finally:
        os.environ[config.DB_ENV_VAR] = previous

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "service_unavailable"
    assert "import_data.py" in error["message"]


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------


def test_stats_match_the_dataset(client: TestClient) -> None:
    body = client.get(STATS).json()
    assert body["total_customers"] == TOTAL
    assert body["age"] == {"min": 18, "max": 70, "avg": 38.85}
    assert body["annual_income_k"] == {"min": 15, "max": 137, "avg": 60.56}
    assert body["spending_score"] == {"min": 1, "max": 99, "avg": 50.2}

    counts = {row["gender"]: row["count"] for row in body["by_gender"]}
    assert counts == {"Female": FEMALE_COUNT, "Male": MALE_COUNT}

    assert sum(row["count"] for row in body["by_segment"]) == TOTAL
    assert {row["segment"] for row in body["by_segment"]} == {
        "careless",
        "frugal",
        "target",
        "cautious",
        "standard",
    }
