from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_customer_list_is_paginated(client: TestClient) -> None:
    response = client.get("/customers", params={"page": 2, "page_size": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 200
    assert body["total_pages"] == 40
    assert body["page"] == 2
    assert len(body["items"]) == 5
    assert body["items"][0]["customer_id"] == "0006"


def test_filters_can_be_combined(client: TestClient) -> None:
    response = client.get(
        "/customers",
        params={
            "gender": "Female",
            "min_age": 30,
            "max_age": 35,
            "min_spending_score": 70,
            "page_size": 100,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    assert all(item["gender"] == "Female" for item in body["items"])
    assert all(30 <= item["age"] <= 35 for item in body["items"])
    assert all(item["spending_score"] >= 70 for item in body["items"])


def test_search_matches_customer_id(client: TestClient) -> None:
    response = client.get("/customers", params={"q": "0001"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["customer_id"] == "0001"


def test_customer_lookup_returns_not_found_error(client: TestClient) -> None:
    response = client.get("/customers/9999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "customer_not_found"


def test_invalid_pagination_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/customers", params={"page_size": 101})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_reversed_filter_range_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/customers", params={"min_annual_income": 80, "max_annual_income": 20}
    )

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "invalid_range",
        "message": "min_annual_income cannot exceed max_annual_income.",
    }
