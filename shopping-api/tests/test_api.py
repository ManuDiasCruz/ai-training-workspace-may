from pathlib import Path

from fastapi.testclient import TestClient

from shopping_api.main import create_app


def test_list_filter_search_and_validation(tmp_path: Path) -> None:
    csv_path = Path(__file__).parents[1] / "data" / "Shopping_data.csv"
    app = create_app(tmp_path / "test.db", csv_path)

    with TestClient(app) as client:
        first_page = client.get("/customers?page=2&page_size=5")
        assert first_page.status_code == 200
        assert first_page.json()["total"] == 200
        assert first_page.json()["items"][0]["customer_id"] == "0006"

        filtered = client.get(
            "/customers?genre=female&min_age=20&max_age=20&search=Female"
        )
        assert filtered.status_code == 200
        assert {item["customer_id"] for item in filtered.json()["items"]} == {
            "0003",
            "0040",
        }

        invalid = client.get("/customers?min_age=40&max_age=20")
        assert invalid.status_code == 400

        missing = client.get("/customers/9999")
        assert missing.status_code == 404
