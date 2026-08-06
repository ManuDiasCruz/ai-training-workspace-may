"""Behavioral and failure-path coverage for the shopping API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from shop_api.import_data import DEFAULT_CSV_PATH, DatasetImportError, import_dataset
from shop_api.main import app


@pytest.fixture()
def database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "customers.sqlite3"
    monkeypatch.setenv("SHOP_API_DATABASE", str(path))
    import_dataset(DEFAULT_CSV_PATH, path)
    return path


@pytest.fixture()
def client(database_path: Path) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_all_imported_customers(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected",
        "customer_count": 200,
    }


def test_customer_listing_paginates_and_preserves_zero_padded_ids(
    client: TestClient,
) -> None:
    response = client.get("/customers", params={"page": 2, "page_size": 3})

    assert response.status_code == 200
    payload = response.json()
    assert [customer["customer_id"] for customer in payload["items"]] == [
        "0004",
        "0005",
        "0006",
    ]
    assert payload["pagination"] == {
        "page": 2,
        "page_size": 3,
        "total_items": 200,
        "total_pages": 67,
        "has_next": True,
        "has_previous": True,
    }


def test_customer_listing_combines_gender_age_income_and_score_filters(
    client: TestClient,
) -> None:
    response = client.get(
        "/customers",
        params={
            "gender": "female",
            "min_age": 30,
            "max_age": 35,
            "min_income": 70,
            "max_income": 80,
            "min_spending_score": 70,
        },
    )

    assert response.status_code == 200
    customers = response.json()["items"]
    assert customers
    assert all(
        customer["gender"] == "Female"
        and 30 <= customer["age"] <= 35
        and 70 <= customer["annual_income_k_usd"] <= 80
        and customer["spending_score"] >= 70
        for customer in customers
    )


@pytest.mark.parametrize(
    ("query", "expected_count"),
    [
        ("0001", 1),
        ("FEMALE", 112),
        ("%", 0),
        ("_", 0),
    ],
)
def test_search_is_case_insensitive_and_treats_wildcards_literally(
    client: TestClient,
    query: str,
    expected_count: int,
) -> None:
    response = client.get("/customers", params={"q": query})

    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == expected_count


def test_customer_detail_returns_the_original_customer(client: TestClient) -> None:
    response = client.get("/customers/0001")

    assert response.status_code == 200
    assert response.json() == {
        "customer_id": "0001",
        "gender": "Male",
        "age": 19,
        "annual_income_k_usd": 15,
        "spending_score": 39,
    }


def test_missing_customer_returns_404(client: TestClient) -> None:
    response = client.get("/customers/9999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.parametrize(
    "parameters",
    [
        {"page": 0},
        {"page_size": 101},
        {"min_age": -1},
        {"min_age": 50, "max_age": 20},
        {"min_income": 80, "max_income": 20},
        {"min_spending_score": 80, "max_spending_score": 20},
        {"gender": "other"},
    ],
)
def test_invalid_filter_or_pagination_returns_422(
    client: TestClient,
    parameters: dict[str, int | str],
) -> None:
    response = client.get("/customers", params=parameters)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_invalid_customer_identifier_returns_422(client: TestClient) -> None:
    response = client.get("/customers/1")

    assert response.status_code == 422


def test_statistics_match_the_source_dataset(client: TestClient) -> None:
    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_customers": 200,
        "gender_breakdown": {"Female": 112, "Male": 88},
        "age": {"minimum": 18, "maximum": 70, "average": 38.85},
        "annual_income_k_usd": {"minimum": 15, "maximum": 137, "average": 60.56},
        "spending_score": {"minimum": 1, "maximum": 99, "average": 50.2},
    }


def test_missing_database_returns_a_clear_503(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SHOP_API_DATABASE", str(tmp_path / "missing.sqlite3"))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert "import_data" in response.json()["detail"]


def test_invalid_import_preserves_existing_dataset(
    database_path: Path,
    tmp_path: Path,
) -> None:
    invalid_csv = tmp_path / "invalid.csv"
    invalid_csv.write_text(
        "CustomerID,Genre,Age,Annual Income (k$),Spending Score (1-100)\n"
        "0001,Female,25,60,999\n",
        encoding="utf-8",
    )

    with pytest.raises(DatasetImportError, match="between 0 and 100"):
        import_dataset(invalid_csv, database_path)

    with TestClient(app) as client:
        assert client.get("/health").json()["customer_count"] == 200

