"""End-to-end API tests over the imported shopping dataset."""

from __future__ import annotations


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database_ready"] is True


def test_list_default_pagination(client):
    response = client.get("/api/v1/customers")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 20
    assert body["pagination"] == {
        "page": 1,
        "page_size": 20,
        "total_items": 200,
        "total_pages": 10,
        "has_next": True,
        "has_prev": False,
    }
    assert body["items"][0]["customer_id"] == 1


def test_second_page_continues_sequence(client):
    response = client.get("/api/v1/customers", params={"page": 2})
    body = response.json()
    assert body["items"][0]["customer_id"] == 21
    assert body["pagination"]["has_prev"] is True


def test_last_page_is_partial(client):
    response = client.get("/api/v1/customers", params={"page": 3, "page_size": 70})
    body = response.json()
    assert len(body["items"]) == 60
    assert body["pagination"]["has_next"] is False


def test_page_beyond_data_is_empty(client):
    response = client.get("/api/v1/customers", params={"page": 99})
    body = response.json()
    assert response.status_code == 200
    assert body["items"] == []
    assert body["pagination"]["has_next"] is False


def test_page_size_above_limit_rejected(client):
    response = client.get("/api/v1/customers", params={"page_size": 500})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == 422
    assert body["error"]["message"] == "Validation failed"


def test_filter_by_genre_case_insensitive(client, csv_rows):
    expected = sum(1 for row in csv_rows if row["genre"] == "Female")
    response = client.get("/api/v1/customers", params={"genre": "female", "page_size": 100})
    body = response.json()
    assert body["pagination"]["total_items"] == expected
    assert all(item["genre"] == "Female" for item in body["items"])


def test_filter_invalid_genre_rejected(client):
    response = client.get("/api/v1/customers", params={"genre": "other"})
    assert response.status_code == 422
    assert "genre" in response.json()["error"]["message"]


def test_filter_age_range(client, csv_rows):
    expected = sum(1 for row in csv_rows if 30 <= row["age"] <= 40)
    response = client.get("/api/v1/customers", params={"min_age": 30, "max_age": 40, "page_size": 100})
    body = response.json()
    assert body["pagination"]["total_items"] == expected
    assert all(30 <= item["age"] <= 40 for item in body["items"])


def test_filter_min_income(client, csv_rows):
    expected = sum(1 for row in csv_rows if row["annual_income_k"] >= 100)
    response = client.get("/api/v1/customers", params={"min_income": 100, "page_size": 100})
    body = response.json()
    assert body["pagination"]["total_items"] == expected
    assert all(item["annual_income_k"] >= 100 for item in body["items"])


def test_filters_combine(client, csv_rows):
    expected = sum(
        1 for row in csv_rows if row["genre"] == "Male" and row["spending_score"] >= 80
    )
    response = client.get(
        "/api/v1/customers", params={"genre": "Male", "min_score": 80, "page_size": 100}
    )
    body = response.json()
    assert body["pagination"]["total_items"] == expected
    assert all(item["genre"] == "Male" and item["spending_score"] >= 80 for item in body["items"])


def test_inverted_range_rejected(client):
    response = client.get("/api/v1/customers", params={"min_age": 50, "max_age": 20})
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == 400
    assert "min_age" in body["error"]["message"]


def test_search_by_padded_id(client):
    response = client.get("/api/v1/customers", params={"q": "0042"})
    body = response.json()
    assert body["pagination"]["total_items"] == 1
    assert body["items"][0]["customer_id"] == 42


def test_search_genre_prefix_does_not_cross_match(client, csv_rows):
    male_count = sum(1 for row in csv_rows if row["genre"] == "Male")
    response = client.get("/api/v1/customers", params={"q": "male", "page_size": 100})
    body = response.json()
    # Prefix semantics: "male" must not match "Female" rows.
    assert body["pagination"]["total_items"] == male_count
    assert all(item["genre"] == "Male" for item in body["items"])


def test_search_like_wildcards_are_literal(client):
    response = client.get("/api/v1/customers", params={"q": "%"})
    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == 0


def test_sort_by_income_desc(client, csv_rows):
    top_income = max(row["annual_income_k"] for row in csv_rows)
    response = client.get(
        "/api/v1/customers", params={"sort_by": "annual_income_k", "sort_order": "desc"}
    )
    body = response.json()
    assert body["items"][0]["annual_income_k"] == top_income
    incomes = [item["annual_income_k"] for item in body["items"]]
    assert incomes == sorted(incomes, reverse=True)


def test_sort_by_unknown_field_rejected(client):
    response = client.get("/api/v1/customers", params={"sort_by": "password"})
    assert response.status_code == 422


def test_get_customer_by_id(client, csv_rows):
    first = csv_rows[0]
    response = client.get("/api/v1/customers/1")
    assert response.status_code == 200
    assert response.json() == first


def test_get_customer_not_found(client):
    response = client.get("/api/v1/customers/9999")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == 404
    assert "9999" in body["error"]["message"]


def test_get_customer_non_numeric_id_rejected(client):
    response = client.get("/api/v1/customers/abc")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == 422


def test_stats_match_dataset(client, csv_rows):
    response = client.get("/api/v1/customers/stats")
    assert response.status_code == 200
    body = response.json()

    ages = [row["age"] for row in csv_rows]
    incomes = [row["annual_income_k"] for row in csv_rows]
    scores = [row["spending_score"] for row in csv_rows]

    assert body["total_customers"] == len(csv_rows)
    assert body["genre_counts"] == {
        "Female": sum(1 for row in csv_rows if row["genre"] == "Female"),
        "Male": sum(1 for row in csv_rows if row["genre"] == "Male"),
    }
    assert body["age"] == {"min": min(ages), "max": max(ages), "avg": round(sum(ages) / len(ages), 2)}
    assert body["annual_income_k"]["min"] == min(incomes)
    assert body["annual_income_k"]["max"] == max(incomes)
    assert body["spending_score"]["min"] == min(scores)
    assert body["spending_score"]["max"] == max(scores)
