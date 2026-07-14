
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_list_customers_supports_pagination_and_filters(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SHOPPING_DATABASE_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        response = client.get(
            "/customers",
            params={
                "page": 1,
                "page_size": 3,
                "gender": "Female",
                "age_max": 25,
                "score_min": 70,
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["page_size"] == 3
    assert payload["total"] > 0
    assert len(payload["items"]) <= 3
    assert all(item["gender"] == "Female" for item in payload["items"])
    assert all(item["age"] <= 25 for item in payload["items"])
    assert all(item["spending_score"] >= 70 for item in payload["items"])


def test_search_and_missing_customer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SHOPPING_DATABASE_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        search = client.get("/customers", params={"q": "0001"})
        missing = client.get("/customers/9999")
    assert search.status_code == 200
    assert search.json()["items"][0]["customer_id"] == "0001"
    assert missing.status_code == 404

