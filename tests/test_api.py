def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_stats(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_customers"] == 200
    assert set(body["by_gender"].keys()) == {"Male", "Female"}
    assert 0 < body["avg_age"] < 130
    assert 0 < body["avg_spending_score"] <= 100


def test_list_default_pagination(client):
    r = client.get("/customers")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 200
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total_pages"] == 10
    assert body["has_next"] is True
    assert body["has_previous"] is False
    assert len(body["items"]) == 20
    assert body["items"][0]["customer_code"] == "0001"


def test_list_pagination_second_page(client):
    r = client.get("/customers?page=2&page_size=50")
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 50
    assert body["items"][0]["customer_code"] == "0051"


def test_filter_by_gender(client):
    r = client.get("/customers?gender=Female&page_size=200")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0
    assert all(item["gender"] == "Female" for item in body["items"])


def test_filter_by_age_range(client):
    r = client.get("/customers?min_age=20&max_age=25&page_size=200")
    assert r.status_code == 200
    body = r.json()
    assert all(20 <= item["age"] <= 25 for item in body["items"])


def test_filter_validation_error(client):
    r = client.get("/customers?min_age=50&max_age=20")
    assert r.status_code == 400


def test_search(client):
    r = client.get("/customers?search=0042")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["customer_code"] == "0042"


def test_sort_by_spending_score_desc(client):
    r = client.get("/customers?sort_by=spending_score&order=desc&page_size=5")
    assert r.status_code == 200
    scores = [it["spending_score"] for it in r.json()["items"]]
    assert scores == sorted(scores, reverse=True)


def test_get_single_customer(client):
    r = client.get("/customers/1")
    assert r.status_code == 200
    assert r.json()["customer_code"] == "0001"


def test_get_missing_customer(client):
    r = client.get("/customers/999999")
    assert r.status_code == 404


def test_update_customer(client):
    r = client.patch(
        "/customers/1", json={"annual_income_k": 25, "spending_score": 75}
    )
    assert r.status_code == 200
    assert r.json()["customer_code"] == "0001"
    assert r.json()["annual_income_k"] == 25
    assert r.json()["spending_score"] == 75

    empty_update = client.patch("/customers/1", json={})
    assert empty_update.status_code == 400

    missing = client.patch("/customers/999999", json={"age": 30})
    assert missing.status_code == 404


def test_create_and_delete_customer(client):
    new_payload = {
        "customer_code": "9999",
        "gender": "Female",
        "age": 28,
        "annual_income_k": 60,
        "spending_score": 55,
    }
    r = client.post("/customers", json=new_payload)
    assert r.status_code == 201
    created = r.json()
    assert created["customer_code"] == "9999"

    r2 = client.post("/customers", json=new_payload)
    assert r2.status_code == 409

    cid = created["id"]
    r3 = client.delete(f"/customers/{cid}")
    assert r3.status_code == 204
    r4 = client.get(f"/customers/{cid}")
    assert r4.status_code == 404


def test_create_invalid_payload(client):
    bad = {
        "customer_code": "X",
        "gender": "Other",
        "age": 25,
        "annual_income_k": 30,
        "spending_score": 50,
    }
    r = client.post("/customers", json=bad)
    assert r.status_code == 422
