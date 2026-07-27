from pathlib import Path

from fastapi.testclient import TestClient

from app.config import PROJECT_ROOT
from app.importer import import_csv
from app.main import app


def test_list_filter_search_and_validation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SHOPPING_DB_PATH", str(tmp_path / "test.db"))
    imported = import_csv(PROJECT_ROOT / "data" / "Shopping_data.csv")
    assert imported == 200

    with TestClient(app) as client:
        response = client.get(
            "/customers",
            params={
                "page": 1,
                "page_size": 5,
                "gender": "Female",
                "min_spending_score": 90,
                "q": "female",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["page_size"] == 5
        assert payload["total"] > 0
        assert len(payload["items"]) <= 5
        assert all(item["gender"] == "Female" for item in payload["items"])
        assert all(item["spending_score"] >= 90 for item in payload["items"])

        detail = client.get("/customers/0001")
        assert detail.status_code == 200
        assert detail.json()["customer_id"] == "0001"

        invalid_range = client.get("/customers", params={"min_age": 50, "max_age": 20})
        assert invalid_range.status_code == 422

        missing = client.get("/customers/9999")
        assert missing.status_code == 404
