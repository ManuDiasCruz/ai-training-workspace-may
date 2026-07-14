"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database seeded from the real
dataset CSV, so they never touch the developer's local ``shopping.db``.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Customer

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "Shopping_data.csv"


def _seed(session) -> None:
    with DATA_FILE.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]  # type: ignore[assignment]
        session.add_all(
            Customer(
                customer_id=row["CustomerID"].strip(),
                gender=row["Genre"].strip(),
                age=int(row["Age"]),
                annual_income=int(row["Annual Income (k$)"]),
                spending_score=int(row["Spending Score (1-100)"]),
            )
            for row in reader
        )
        session.commit()


@pytest.fixture(scope="session")
def client() -> TestClient:
    # A single in-memory database shared across connections for the test session.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(engine)
    with TestingSession() as session:
        _seed(session)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
