from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from shopping_api.database import connect, import_csv, initialize_database


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "shopping.db"
DEFAULT_CSV = PROJECT_ROOT / "data" / "Shopping_data.csv"


class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    genre: str
    age: int
    annual_income_kusd: int
    spending_score: int


class CustomerPage(BaseModel):
    items: list[Customer]
    page: int
    page_size: int
    total: int
    pages: int


def create_app(
    database_path: Path | None = None,
    csv_path: Path | None = None,
    auto_import: bool = True,
) -> FastAPI:
    selected_database = Path(
        database_path or os.getenv("SHOPPING_DATABASE", DEFAULT_DATABASE)
    )
    selected_csv = Path(csv_path or os.getenv("SHOPPING_CSV", DEFAULT_CSV))

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(selected_database)
        with connect(selected_database) as connection:
            row_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if auto_import and row_count == 0 and selected_csv.exists():
            import_csv(selected_csv, selected_database)
        yield

    app = FastAPI(
        title="Shopping Customer API",
        version="1.0.0",
        description="Paginated access to the persisted shopping customer dataset.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        with connect(selected_database) as connection:
            connection.execute("SELECT 1")
        return {"status": "ok"}

    @app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
    def get_customer(customer_id: str) -> dict:
        with connect(selected_database) as connection:
            row = connection.execute(
                """
                SELECT customer_id, genre, age, annual_income_kusd, spending_score
                FROM customers WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return dict(row)

    @app.get("/customers", response_model=CustomerPage, tags=["customers"])
    def list_customers(
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
        genre: Annotated[str | None, Query(pattern="(?i)^(male|female)$")] = None,
        min_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        max_age: Annotated[int | None, Query(ge=0, le=120)] = None,
        min_annual_income: Annotated[int | None, Query(ge=0)] = None,
        max_annual_income: Annotated[int | None, Query(ge=0)] = None,
        min_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        max_spending_score: Annotated[int | None, Query(ge=1, le=100)] = None,
        search: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
    ) -> dict:
        ranges = [
            ("age", min_age, max_age),
            ("annual income", min_annual_income, max_annual_income),
            ("spending score", min_spending_score, max_spending_score),
        ]
        for label, minimum, maximum in ranges:
            if minimum is not None and maximum is not None and minimum > maximum:
                raise HTTPException(
                    status_code=400,
                    detail=f"Minimum {label} cannot exceed maximum {label}",
                )

        clauses: list[str] = []
        params: list[object] = []
        field_filters = [
            ("age >= ?", min_age),
            ("age <= ?", max_age),
            ("annual_income_kusd >= ?", min_annual_income),
            ("annual_income_kusd <= ?", max_annual_income),
            ("spending_score >= ?", min_spending_score),
            ("spending_score <= ?", max_spending_score),
        ]
        if genre:
            clauses.append("genre = ? COLLATE NOCASE")
            params.append(genre)
        for clause, value in field_filters:
            if value is not None:
                clauses.append(clause)
                params.append(value)
        if search:
            clauses.append("(customer_id LIKE ? OR genre LIKE ?)")
            term = f"%{search}%"
            params.extend([term, term])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        offset = (page - 1) * page_size
        with connect(selected_database) as connection:
            total = connection.execute(
                f"SELECT COUNT(*) FROM customers {where}", params
            ).fetchone()[0]
            rows = connection.execute(
                f"""
                SELECT customer_id, genre, age, annual_income_kusd, spending_score
                FROM customers {where}
                ORDER BY customer_id
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, offset],
            ).fetchall()

        return {
            "items": [dict(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        }

    return app


app = create_app()
