"""API tests exercising listing, pagination, filtering, search and errors."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_customers_default_pagination(client: TestClient) -> None:
    response = client.get("/customers")
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 200
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total_pages"] == 10
    assert len(body["items"]) == 20
    assert body["items"][0] == {
        "id": 1,
        "genre": "Male",
        "age": 19,
        "annual_income_k": 15,
        "spending_score": 39,
    }


def test_pagination_returns_distinct_pages(client: TestClient) -> None:
    page1 = client.get("/customers", params={"page": 1, "page_size": 5}).json()
    page2 = client.get("/customers", params={"page": 2, "page_size": 5}).json()
    assert [c["id"] for c in page1["items"]] == [1, 2, 3, 4, 5]
    assert [c["id"] for c in page2["items"]] == [6, 7, 8, 9, 10]
    assert page1["total_pages"] == 40


def test_last_page_is_partial_when_needed(client: TestClient) -> None:
    body = client.get("/customers", params={"page": 3, "page_size": 90}).json()
    assert body["total_pages"] == 3
    assert len(body["items"]) == 20


def test_filter_by_genre_is_case_insensitive(client: TestClient) -> None:
    body = client.get("/customers", params={"genre": "female", "page_size": 100}).json()
    assert body["total_items"] == 112
    assert all(c["genre"] == "Female" for c in body["items"])


def test_filter_by_income_range(client: TestClient) -> None:
    body = client.get(
        "/customers", params={"min_income": 100, "max_income": 120, "page_size": 100}
    ).json()
    assert body["total_items"] == 10
    assert all(100 <= c["annual_income_k"] <= 120 for c in body["items"])


def test_combined_filters_and_sorting(client: TestClient) -> None:
    body = client.get(
        "/customers",
        params={
            "genre": "Male",
            "min_score": 90,
            "sort_by": "spending_score",
            "sort_dir": "desc",
        },
    ).json()
    scores = [c["spending_score"] for c in body["items"]]
    assert scores == sorted(scores, reverse=True)
    assert all(c["genre"] == "Male" and c["spending_score"] >= 90 for c in body["items"])


def test_search_by_numeric_id(client: TestClient) -> None:
    body = client.get("/customers", params={"q": "42"}).json()
    assert body["total_items"] == 1
    assert body["items"][0]["id"] == 42


def test_search_by_genre_substring(client: TestClient) -> None:
    body = client.get("/customers", params={"q": "fem", "page_size": 100}).json()
    assert body["total_items"] == 112


def test_get_customer_by_id(client: TestClient) -> None:
    response = client.get("/customers/200")
    assert response.status_code == 200
    assert response.json() == {
        "id": 200,
        "genre": "Male",
        "age": 30,
        "annual_income_k": 137,
        "spending_score": 83,
    }


def test_get_missing_customer_returns_404(client: TestClient) -> None:
    response = client.get("/customers/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_invalid_page_size_returns_422(client: TestClient) -> None:
    assert client.get("/customers", params={"page_size": 0}).status_code == 422
    assert client.get("/customers", params={"page_size": 101}).status_code == 422
    assert client.get("/customers", params={"genre": "Other"}).status_code == 422


def test_inverted_range_returns_400(client: TestClient) -> None:
    response = client.get("/customers", params={"min_age": 50, "max_age": 20})
    assert response.status_code == 400
    assert "min_age" in response.json()["detail"]


def test_stats_endpoint(client: TestClient) -> None:
    response = client.get("/customers/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_customers"] == 200
    assert body["min_annual_income_k"] == 15
    assert body["max_annual_income_k"] == 137
    genres = {g["genre"]: g["count"] for g in body["by_genre"]}
    assert genres == {"Female": 112, "Male": 88}
