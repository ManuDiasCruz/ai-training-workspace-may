"""API tests for listing, pagination, filtering, search and error handling."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

TOTAL_RECORDS = 200
CUSTOMERS = "/api/v1/customers"


# --------------------------------------------------------------------------- #
# health
# --------------------------------------------------------------------------- #


def test_health_reports_ready_database(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database"] == "ready"
    assert body["customer_count"] == TOTAL_RECORDS


def test_database_missing_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """A missing database is an actionable 503, not a 500."""
    monkeypatch.setenv("SHOPAPI_DB_PATH", str(tmp_path / "does_not_exist.db"))

    response = client.get(CUSTOMERS)

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "database_unavailable"
    # The message has to tell the caller how to fix it.
    assert "scripts.import_dataset" in error["message"]

    # /health still answers rather than failing with the database it reports on.
    health = client.get("/health").json()
    assert health["status"] == "degraded"
    assert health["database"] == "missing"


# --------------------------------------------------------------------------- #
# listing and pagination
# --------------------------------------------------------------------------- #


def test_list_returns_default_page(client: TestClient) -> None:
    body = client.get(CUSTOMERS).json()

    assert len(body["items"]) == 20, "default page_size should be 20"
    assert body["pagination"] == {
        "page": 1,
        "page_size": 20,
        "total_items": TOTAL_RECORDS,
        "total_pages": 10,
        "has_next": True,
        "has_previous": False,
    }


def test_record_shape_matches_dataset(client: TestClient, csv_rows) -> None:
    """The first record must round-trip the CSV values, padding included."""
    first = client.get(f"{CUSTOMERS}?page_size=1").json()["items"][0]
    source = csv_rows[0]

    assert first == {
        "customer_id": source["CustomerID"],
        "genre": source["Genre"],
        "age": int(source["Age"]),
        "annual_income_k": int(source["Annual Income (k$)"]),
        "spending_score": int(source["Spending Score (1-100)"]),
    }


def test_paging_covers_every_record_exactly_once(client: TestClient) -> None:
    """Walking every page must yield all 200 records with no gaps or repeats."""
    seen: list[str] = []
    page = 1
    while True:
        body = client.get(f"{CUSTOMERS}?page={page}&page_size=7").json()
        seen.extend(item["customer_id"] for item in body["items"])
        if not body["pagination"]["has_next"]:
            break
        page += 1
        assert page < 100, "pagination failed to terminate"

    assert len(seen) == TOTAL_RECORDS
    assert len(set(seen)) == TOTAL_RECORDS, "a record appeared on more than one page"


def test_paging_is_stable_for_non_unique_sort_key(client: TestClient) -> None:
    """Sorting by a column with duplicates must still page deterministically.

    47 age values repeat in this dataset, so LIMIT/OFFSET paging over `age`
    relies on the ORDER BY being total. This asserts the observable property
    (no record repeated or skipped across pages) rather than the mechanism:
    for this data SQLite's chosen plan happens to be stable even without the
    customer_id tiebreaker, so the test is a regression guard against a plan
    or query change, not proof that the tiebreaker is present.
    """
    seen: list[str] = []
    for page in range(1, 6):
        body = client.get(f"{CUSTOMERS}?sort_by=age&page={page}&page_size=40").json()
        seen.extend(item["customer_id"] for item in body["items"])

    assert len(seen) == TOTAL_RECORDS
    assert len(set(seen)) == TOTAL_RECORDS


def test_page_beyond_last_returns_empty_page_not_error(client: TestClient) -> None:
    body = client.get(f"{CUSTOMERS}?page=99&page_size=100").json()

    assert body["items"] == []
    assert body["pagination"]["total_items"] == TOTAL_RECORDS
    assert body["pagination"]["has_next"] is False


# --------------------------------------------------------------------------- #
# filtering
# --------------------------------------------------------------------------- #


def test_filter_by_genre_matches_dataset_count(client: TestClient, csv_rows) -> None:
    expected = sum(1 for row in csv_rows if row["Genre"] == "Female")

    body = client.get(f"{CUSTOMERS}?genre=Female&page_size=100").json()

    assert body["pagination"]["total_items"] == expected
    assert all(item["genre"] == "Female" for item in body["items"])


def test_filter_bounds_are_inclusive(client: TestClient, csv_rows) -> None:
    expected = sum(1 for row in csv_rows if 30 <= int(row["Age"]) <= 35)

    body = client.get(f"{CUSTOMERS}?min_age=30&max_age=35&page_size=100").json()

    assert body["pagination"]["total_items"] == expected
    assert all(30 <= item["age"] <= 35 for item in body["items"])


def test_filters_combine_with_and(client: TestClient, csv_rows) -> None:
    expected = sum(
        1
        for row in csv_rows
        if row["Genre"] == "Male"
        and int(row["Annual Income (k$)"]) >= 70
        and int(row["Spending Score (1-100)"]) >= 60
    )

    body = client.get(
        f"{CUSTOMERS}?genre=Male&min_income=70&min_score=60&page_size=100"
    ).json()

    assert body["pagination"]["total_items"] == expected
    assert expected > 0, "fixture assumption: this filter should match something"
    for item in body["items"]:
        assert item["genre"] == "Male"
        assert item["annual_income_k"] >= 70
        assert item["spending_score"] >= 60


def test_filter_matching_nothing_returns_empty_page(client: TestClient) -> None:
    body = client.get(f"{CUSTOMERS}?min_age=119").json()

    assert body["items"] == []
    assert body["pagination"]["total_items"] == 0
    assert body["pagination"]["total_pages"] == 0


# --------------------------------------------------------------------------- #
# search
# --------------------------------------------------------------------------- #


def test_search_is_case_insensitive(client: TestClient, csv_rows) -> None:
    expected = sum(1 for row in csv_rows if row["Genre"] == "Female")

    body = client.get(f"{CUSTOMERS}?q=fEmAlE&page_size=1").json()

    assert body["pagination"]["total_items"] == expected


def test_search_matches_identifier_fragment(client: TestClient) -> None:
    body = client.get(f"{CUSTOMERS}?q=019&page_size=100").json()

    ids = [item["customer_id"] for item in body["items"]]
    assert ids, "expected identifiers containing '019'"
    assert all("019" in customer_id for customer_id in ids)
    assert "0190" in ids and "0019" in ids, "substring search should match either position"


def test_search_treats_wildcards_literally(client: TestClient) -> None:
    """'%' must be searched for, not interpreted as a LIKE wildcard.

    Unescaped, this would match every row in the table.
    """
    body = client.get(f"{CUSTOMERS}?q=%25").json()

    assert body["pagination"]["total_items"] == 0


# --------------------------------------------------------------------------- #
# sorting
# --------------------------------------------------------------------------- #


def test_sort_descending_by_income(client: TestClient, csv_rows) -> None:
    highest = max(int(row["Annual Income (k$)"]) for row in csv_rows)

    items = client.get(
        f"{CUSTOMERS}?sort_by=annual_income_k&order=desc&page_size=10"
    ).json()["items"]

    incomes = [item["annual_income_k"] for item in items]
    assert incomes[0] == highest
    assert incomes == sorted(incomes, reverse=True)


# --------------------------------------------------------------------------- #
# single record
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("identifier", ["0007", "7", "07"])
def test_get_customer_accepts_padded_and_unpadded_ids(
    client: TestClient, identifier: str
) -> None:
    body = client.get(f"{CUSTOMERS}/{identifier}").json()

    # The response always reports the canonical padded form.
    assert body["customer_id"] == "0007"


def test_get_unknown_customer_returns_404(client: TestClient) -> None:
    response = client.get(f"{CUSTOMERS}/9999")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert "9999" in error["message"]


def test_non_numeric_id_is_rejected_as_invalid_not_missing(client: TestClient) -> None:
    """A malformed identifier is a 422 about its format; 404 would imply such
    an identifier could legitimately exist."""
    response = client.get(f"{CUSTOMERS}/not-an-id")

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "customer_id"


# --------------------------------------------------------------------------- #
# validation and error handling
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("query", "expected_field"),
    [
        ("page=0", "page"),
        ("page=-1", "page"),
        ("page=abc", "page"),
        ("page_size=0", "page_size"),
        ("page_size=101", "page_size"),
        ("genre=Other", "genre"),
        ("min_age=-5", "min_age"),
        ("max_age=200", "max_age"),
        ("min_score=0", "min_score"),
        ("max_score=101", "max_score"),
        ("sort_by=customer_id;DROP+TABLE+customers", "sort_by"),
        ("order=sideways", "order"),
        ("q=", "q"),
    ],
)
def test_invalid_parameters_return_422_naming_the_field(
    client: TestClient, query: str, expected_field: str
) -> None:
    response = client.get(f"{CUSTOMERS}?{query}")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert expected_field in {detail["field"] for detail in error["details"]}


def test_unknown_parameter_is_rejected_not_ignored(client: TestClient) -> None:
    """A typo'd filter must fail loudly rather than return an unfiltered page
    that the caller would read as a filtered one."""
    response = client.get(f"{CUSTOMERS}?min_agee=30")

    assert response.status_code == 422
    assert "min_agee" in {d["field"] for d in response.json()["error"]["details"]}


@pytest.mark.parametrize(
    "query",
    ["min_age=50&max_age=30", "min_income=100&max_income=20", "min_score=90&max_score=10"],
)
def test_inverted_range_is_rejected(client: TestClient, query: str) -> None:
    response = client.get(f"{CUSTOMERS}?{query}")

    assert response.status_code == 422
    assert "cannot be greater than" in str(response.json()["error"]["details"])


def test_errors_share_one_envelope(client: TestClient) -> None:
    """Every failure shape is {"error": {code, message}} so clients parse once."""
    for path in [f"{CUSTOMERS}/9999", f"{CUSTOMERS}?page=0", "/api/v1/nope"]:
        body = client.get(path).json()
        assert set(body) == {"error"}, path
        assert {"code", "message"} <= set(body["error"]), path


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #


def test_stats_agree_with_the_source_csv(client: TestClient, csv_rows) -> None:
    body = client.get("/api/v1/stats").json()

    ages = [int(row["Age"]) for row in csv_rows]
    assert body["total_customers"] == len(csv_rows)
    assert body["age"]["min"] == min(ages)
    assert body["age"]["max"] == max(ages)
    assert body["age"]["mean"] == pytest.approx(sum(ages) / len(ages), abs=0.01)

    by_genre = {entry["genre"]: entry for entry in body["genre_breakdown"]}
    for genre in ("Male", "Female"):
        expected = sum(1 for row in csv_rows if row["Genre"] == genre)
        assert by_genre[genre]["count"] == expected
        assert by_genre[genre]["share_pct"] == pytest.approx(
            expected * 100 / len(csv_rows), abs=0.01
        )

    # Segments partition the dataset: every record lands in exactly one band.
    assert sum(segment["count"] for segment in body["spending_segments"]) == len(csv_rows)


def test_stats_report_import_provenance(client: TestClient) -> None:
    last_import = client.get("/api/v1/stats").json()["last_import"]

    assert last_import is not None
    assert last_import["row_count"] == TOTAL_RECORDS
    assert len(last_import["source_sha256"]) == 64


# --------------------------------------------------------------------------- #
# documentation
# --------------------------------------------------------------------------- #


def test_openapi_schema_documents_every_endpoint(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert {"/health", CUSTOMERS, f"{CUSTOMERS}/{{customer_id}}", "/api/v1/stats"} <= set(paths)
