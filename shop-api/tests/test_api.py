"""End-to-end tests for the Shop API HTTP surface."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from .conftest import TOTAL_ROWS

CUSTOMERS = "/api/v1/customers"


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------


def test_health_reports_loaded_data(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["data_loaded"] is True
    assert body["customers"] == TOTAL_ROWS
    assert body["last_import"]["rows_imported"] == TOTAL_ROWS


def test_root_lists_endpoints(client: TestClient) -> None:
    body = client.get("/").json()
    assert body["service"] == "Shop API"
    assert CUSTOMERS in body["endpoints"]


# --------------------------------------------------------------------------
# Listing and pagination
# --------------------------------------------------------------------------


def test_list_defaults_to_first_page_of_twenty(client: TestClient) -> None:
    body = client.get(CUSTOMERS).json()
    assert len(body["data"]) == 20
    assert body["pagination"] == {
        "page": 1,
        "page_size": 20,
        "total_items": TOTAL_ROWS,
        "total_pages": 10,
        "has_next": True,
        "has_prev": False,
    }
    assert body["data"][0]["customer_ref"] == "0001"


def test_customer_shape_includes_derived_segments(client: TestClient) -> None:
    first = client.get(CUSTOMERS, params={"page_size": 1}).json()["data"][0]
    assert first == {
        "id": 1,
        "customer_ref": "0001",
        "gender": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
        "age_bracket": "under-25",
        "income_band": "low",
        "spending_tier": "medium",
    }


def test_pages_are_disjoint_and_cover_the_dataset(client: TestClient) -> None:
    seen: list[int] = []
    for page in range(1, 5):
        body = client.get(CUSTOMERS, params={"page": page, "page_size": 50}).json()
        seen.extend(row["id"] for row in body["data"])
    assert sorted(seen) == list(range(1, TOTAL_ROWS + 1))
    assert len(set(seen)) == TOTAL_ROWS


def test_last_page_has_no_next(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"page": 10, "page_size": 20}).json()
    assert body["pagination"]["has_next"] is False
    assert body["pagination"]["has_prev"] is True
    assert body["data"][-1]["customer_ref"] == "0200"


def test_page_past_the_end_is_empty_not_an_error(client: TestClient) -> None:
    response = client.get(CUSTOMERS, params={"page": 99, "page_size": 20})
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["pagination"]["total_items"] == TOTAL_ROWS


# --------------------------------------------------------------------------
# Filtering
# --------------------------------------------------------------------------


def test_filter_by_gender_matches_dataset(client: TestClient, csv_rows: list[dict[str, str]]) -> None:
    expected = sum(1 for row in csv_rows if row["Genre"] == "Female")
    body = client.get(CUSTOMERS, params={"gender": "Female", "page_size": 100}).json()
    assert body["pagination"]["total_items"] == expected
    assert {row["gender"] for row in body["data"]} == {"Female"}


def test_filter_by_age_range(client: TestClient, csv_rows: list[dict[str, str]]) -> None:
    expected = sum(1 for row in csv_rows if 30 <= int(row["Age"]) <= 40)
    body = client.get(CUSTOMERS, params={"min_age": 30, "max_age": 40, "page_size": 100}).json()
    assert body["pagination"]["total_items"] == expected
    assert all(30 <= row["age"] <= 40 for row in body["data"])


def test_filter_by_income_band(client: TestClient, csv_rows: list[dict[str, str]]) -> None:
    expected = sum(1 for row in csv_rows if int(row["Annual Income (k$)"]) >= 80)
    body = client.get(CUSTOMERS, params={"income_band": "high", "page_size": 100}).json()
    assert body["pagination"]["total_items"] == expected
    assert all(row["annual_income_k"] >= 80 for row in body["data"])


def test_filters_combine_and_are_echoed_back(client: TestClient) -> None:
    params = {"gender": "Male", "income_band": "high", "min_spending_score": 70, "page_size": 100}
    body = client.get(CUSTOMERS, params=params).json()
    assert body["filters_applied"] == {
        "gender": "Male",
        "income_band": "high",
        "min_spending_score": 70,
    }
    for row in body["data"]:
        assert row["gender"] == "Male"
        assert row["income_band"] == "high"
        assert row["spending_score"] >= 70


def test_filter_with_no_matches_returns_empty_page(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"min_age": 100, "max_age": 120}).json()
    assert body["data"] == []
    assert body["pagination"]["total_items"] == 0
    assert body["pagination"]["total_pages"] == 0
    assert body["pagination"]["has_prev"] is False


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------


def test_search_by_customer_reference(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"q": "0042"}).json()
    assert [row["customer_ref"] for row in body["data"]] == ["0042"]


def test_search_matches_segment_labels(client: TestClient, csv_rows: list[dict[str, str]]) -> None:
    body = client.get(CUSTOMERS, params={"q": "under-25", "page_size": 100}).json()
    expected = sum(1 for row in csv_rows if int(row["Age"]) < 25)
    assert body["pagination"]["total_items"] == expected
    assert all(row["age_bracket"] == "under-25" for row in body["data"])


def test_search_is_a_substring_match(client: TestClient) -> None:
    """Documented behaviour: 'male' also matches 'Female', which contains it.

    Substring search is deliberate (it makes partial refs like '004' work), so
    this pins the consequence rather than pretending it does not exist.
    """
    body = client.get(CUSTOMERS, params={"q": "male", "page_size": 100}).json()
    assert body["pagination"]["total_items"] == TOTAL_ROWS


def test_search_is_case_insensitive(client: TestClient) -> None:
    lower = client.get(CUSTOMERS, params={"q": "under-25"}).json()["pagination"]["total_items"]
    upper = client.get(CUSTOMERS, params={"q": "UNDER-25"}).json()["pagination"]["total_items"]
    assert lower == upper > 0


def test_search_wildcards_are_treated_literally(client: TestClient) -> None:
    """A '%' must not turn into a match-everything pattern."""
    body = client.get(CUSTOMERS, params={"q": "%"}).json()
    assert body["pagination"]["total_items"] == 0


def test_search_combines_with_filters(client: TestClient) -> None:
    body = client.get(CUSTOMERS, params={"q": "high", "gender": "Female", "page_size": 100}).json()
    assert body["pagination"]["total_items"] > 0
    for row in body["data"]:
        assert row["gender"] == "Female"
        assert "high" in (row["income_band"], row["spending_tier"])


# --------------------------------------------------------------------------
# Sorting
# --------------------------------------------------------------------------


def test_sort_by_spending_score_descending(client: TestClient, csv_rows: list[dict[str, str]]) -> None:
    body = client.get(
        CUSTOMERS, params={"sort_by": "spending_score", "order": "desc", "page_size": 100}
    ).json()
    scores = [row["spending_score"] for row in body["data"]]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == max(int(row["Spending Score (1-100)"]) for row in csv_rows)


def test_sort_is_stable_across_pages(client: TestClient) -> None:
    """Ties are broken by id, so paging a sorted list cannot repeat a row."""
    ids: list[int] = []
    for page in (1, 2, 3, 4):
        body = client.get(
            CUSTOMERS, params={"sort_by": "gender", "page": page, "page_size": 50}
        ).json()
        ids.extend(row["id"] for row in body["data"])
    assert len(set(ids)) == TOTAL_ROWS


# --------------------------------------------------------------------------
# Detail
# --------------------------------------------------------------------------


def test_get_customer_by_padded_reference(client: TestClient) -> None:
    body = client.get(f"{CUSTOMERS}/0007").json()
    assert body["customer_ref"] == "0007"
    assert body["id"] == 7


def test_get_customer_by_plain_id(client: TestClient) -> None:
    assert client.get(f"{CUSTOMERS}/7").json() == client.get(f"{CUSTOMERS}/0007").json()


def test_unknown_customer_returns_404_envelope(client: TestClient) -> None:
    response = client.get(f"{CUSTOMERS}/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "customer_not_found"


def test_unknown_route_returns_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    assert "error" in response.json()


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------


def test_stats_match_the_source_dataset(client: TestClient, csv_rows: list[dict[str, str]]) -> None:
    body = client.get("/api/v1/stats").json()
    ages = [int(row["Age"]) for row in csv_rows]

    assert body["total_customers"] == TOTAL_ROWS
    assert body["age"]["min"] == min(ages)
    assert body["age"]["max"] == max(ages)
    assert body["age"]["avg"] == pytest.approx(sum(ages) / len(ages), abs=0.01)

    assert sum(group["count"] for group in body["by_gender"]) == TOTAL_ROWS
    assert sum(group["count"] for group in body["by_income_band"]) == TOTAL_ROWS
    assert {group["value"] for group in body["by_spending_tier"]} == {"low", "medium", "high"}


# --------------------------------------------------------------------------
# Validation and error handling
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": -1},
        {"page_size": 0},
        {"page_size": 101},
        {"gender": "Other"},
        {"income_band": "enormous"},
        {"age_bracket": "90-plus"},
        {"sort_by": "spending_score; DROP TABLE customers"},
        {"order": "sideways"},
        {"min_age": 200},
        {"max_spending_score": 0},
        {"q": ""},
        {"q": "x" * 65},
        {"page": "abc"},
    ],
)
def test_invalid_parameters_are_rejected(client: TestClient, params: dict[str, object]) -> None:
    response = client.get(CUSTOMERS, params=params)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"], "a validation error should name the offending field"


def test_rejected_sort_injection_leaves_data_intact(client: TestClient) -> None:
    client.get(CUSTOMERS, params={"sort_by": "id; DROP TABLE customers"})
    assert client.get(CUSTOMERS).json()["pagination"]["total_items"] == TOTAL_ROWS


@pytest.mark.parametrize(
    "params",
    [
        {"min_age": 50, "max_age": 20},
        {"min_income": 90, "max_income": 30},
        {"min_spending_score": 80, "max_spending_score": 10},
    ],
)
def test_contradictory_ranges_return_400(client: TestClient, params: dict[str, int]) -> None:
    response = client.get(CUSTOMERS, params=params)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_range"


def test_invalid_customer_id_is_rejected(client: TestClient) -> None:
    assert client.get(f"{CUSTOMERS}/0").status_code == 422
    assert client.get(f"{CUSTOMERS}/abc").status_code == 422


def test_missing_database_reports_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Settings are read per request, so pointing at an empty file must degrade cleanly."""
    monkeypatch.setenv("SHOP_API_DB_PATH", str(tmp_path / "absent.db"))

    response = client.get(CUSTOMERS)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_not_initialised"

    health = client.get("/health").json()
    assert health["status"] == "degraded"
    assert health["data_loaded"] is False
