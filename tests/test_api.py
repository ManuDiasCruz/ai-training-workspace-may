import httpx
import pytest

pytestmark = pytest.mark.anyio


async def test_health_reports_imported_dataset(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "customer_count": 200}


async def test_list_customers_is_paginated(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/customers", params={"page": 2, "page_size": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 200
    assert body["pages"] == 67
    assert [item["customer_id"] for item in body["items"]] == ["0004", "0005", "0006"]


async def test_combined_filters_and_search(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/api/v1/customers",
        params={"genre": "male", "min_income": 120, "min_spending_score": 70, "q": "020"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0] == {
        "customer_id": "0200",
        "genre": "Male",
        "age": 30,
        "annual_income_k": 137,
        "spending_score": 83,
    }


async def test_get_customer_and_not_found(client: httpx.AsyncClient) -> None:
    found = await client.get("/api/v1/customers/0001")
    missing = await client.get("/api/v1/customers/9999")

    assert found.status_code == 200
    assert found.json()["customer_id"] == "0001"
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Customer '9999' not found"}


async def test_invalid_filter_ranges_are_rejected(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/api/v1/customers", params={"min_age": 50, "max_age": 30}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "age minimum cannot exceed maximum"}


async def test_query_validation_has_stable_error_shape(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/customers", params={"page_size": 101})

    assert response.status_code == 422
    assert response.json()["detail"].startswith("Invalid page_size:")
