from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.database import import_customers_from_csv
from app.main import create_app


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "Shopping_data.csv"


@pytest.fixture()
def app_with_data(tmp_path):
    db_path = tmp_path / "shopping.db"
    import_customers_from_csv(csv_path=CSV_PATH, db_path=db_path)
    return create_app(db_path=db_path, csv_path=CSV_PATH)


def _request_for(app):
    return SimpleNamespace(app=app)


def _get_endpoint(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path and "GET" in getattr(route, "methods", []):
            return route.endpoint
    raise AssertionError(f"GET {path} route not found")


def test_list_customers_filters_searches_and_paginates(app_with_data):
    endpoint = _get_endpoint(app_with_data, "/customers")

    response = endpoint(
        request=_request_for(app_with_data),
        page=1,
        per_page=3,
        genre="Female",
        min_age=20,
        max_age=40,
        min_income=None,
        max_income=None,
        min_spending_score=70,
        max_spending_score=None,
        q="female",
        sort_by="customer_id",
        sort_order="asc",
    )

    assert response.pagination.page == 1
    assert response.pagination.per_page == 3
    assert response.pagination.total > 3
    assert len(response.data) == 3
    assert all(customer.genre == "Female" for customer in response.data)
    assert all(20 <= customer.age <= 40 for customer in response.data)
    assert all(customer.spending_score >= 70 for customer in response.data)


def test_get_customer_by_id_and_not_found(app_with_data):
    endpoint = _get_endpoint(app_with_data, "/customers/{customer_id}")

    customer = endpoint(request=_request_for(app_with_data), customer_id="0001")
    assert customer.customer_id == "0001"
    assert customer.genre == "Male"
    assert customer.age == 19

    with pytest.raises(HTTPException) as exc_info:
        endpoint(request=_request_for(app_with_data), customer_id="9999")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Customer not found"


def test_list_customers_rejects_invalid_ranges(app_with_data):
    endpoint = _get_endpoint(app_with_data, "/customers")

    with pytest.raises(HTTPException) as exc_info:
        endpoint(
            request=_request_for(app_with_data),
            page=1,
            per_page=25,
            genre=None,
            min_age=70,
            max_age=20,
            min_income=None,
            max_income=None,
            min_spending_score=None,
            max_spending_score=None,
            q=None,
            sort_by="customer_id",
            sort_order="asc",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "age minimum cannot be greater than maximum"

