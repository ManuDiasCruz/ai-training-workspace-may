from fastapi.testclient import TestClient

from app.import_data import DEFAULT_CSV_PATH, import_csv
from app.main import create_app


def build_client(tmp_path) -> TestClient:
    database_path = tmp_path / "shopping-test.db"
    import_csv(DEFAULT_CSV_PATH, database_path)
    return TestClient(create_app(database_path))


def test_list_customers_supports_pagination_filters_and_search(tmp_path) -> None:
    with build_client(tmp_path) as client:
        response = client.get(
            "/customers",
            params={
                "page": 1,
                "page_size": 5,
                "genre": "female",
                "min_annual_income": 70,
                "min_spending_score": 70,
                "q": "female",
                "sort_by": "spending_score",
                "sort_order": "desc",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 5
    assert payload["total"] > 5
    assert len(payload["items"]) == 5
    assert payload["pages"] >= 2
    assert all(item["genre"] == "Female" for item in payload["items"])
    assert all(item["annual_income_k"] >= 70 for item in payload["items"])
    assert all(item["spending_score"] >= 70 for item in payload["items"])
    scores = [item["spending_score"] for item in payload["items"]]
    assert scores == sorted(scores, reverse=True)


def test_get_customer_and_not_found(tmp_path) -> None:
    with build_client(tmp_path) as client:
        found = client.get("/customers/0001")
        missing = client.get("/customers/9999")

    assert found.status_code == 200
    assert found.json() == {
        "customer_id": "0001",
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }
    assert missing.status_code == 404


def test_invalid_filter_range_returns_validation_error(tmp_path) -> None:
    with build_client(tmp_path) as client:
        response = client.get(
            "/customers", params={"min_age": 60, "max_age": 20}
        )

    assert response.status_code == 422
    assert "minimum" in response.json()["detail"]


def test_health_reports_imported_row_count(tmp_path) -> None:
    with build_client(tmp_path) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ready",
        "customer_count": 200,
    }
