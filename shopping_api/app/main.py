"""REST API for querying the persisted shopping customer dataset."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from shopping_api.app.database import (
    DatabaseNotReadyError,
    get_database_path,
    open_database,
)
from shopping_api.app.models import (
    Customer,
    CustomerList,
    DatasetMetadata,
    Gender,
    Health,
    Pagination,
)

app = FastAPI(
    title="Shopping Customer Dataset API",
    version="1.0.0",
    description=(
        "Read-only, paginated access to the Drive-sourced shopping customer "
        "dataset persisted in SQLite."
    ),
)


@app.exception_handler(DatabaseNotReadyError)
async def database_not_ready_handler(
    _request: Request, exc: DatabaseNotReadyError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def _customer_from_row(row: Any) -> Customer:
    return Customer.model_validate(dict(row))


def _validate_range(
    minimum: int | None,
    maximum: int | None,
    minimum_name: str,
    maximum_name: str,
) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=422,
            detail=f"{minimum_name} cannot be greater than {maximum_name}.",
        )


def _literal_search_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@app.get("/health", response_model=Health, tags=["system"])
def health() -> Health:
    with open_database() as connection:
        count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return Health(
        status="ok",
        database=get_database_path().name,
        customer_count=count,
    )


@app.get("/api/v1/metadata", response_model=DatasetMetadata, tags=["dataset"])
def dataset_metadata() -> DatasetMetadata:
    with open_database() as connection:
        row = connection.execute(
            """
            SELECT source_file, source_url, source_modified_at,
                   imported_at, record_count
            FROM dataset_metadata
            WHERE singleton_id = 1
            """
        ).fetchone()
    if row is None:
        raise DatabaseNotReadyError("Dataset metadata is missing; re-run the import.")
    return DatasetMetadata.model_validate(dict(row))


@app.get("/api/v1/customers", response_model=CustomerList, tags=["customers"])
def list_customers(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    gender: Gender | None = None,
    age_min: Annotated[int | None, Query(ge=0, le=120)] = None,
    age_max: Annotated[int | None, Query(ge=0, le=120)] = None,
    income_min: Annotated[int | None, Query(ge=0)] = None,
    income_max: Annotated[int | None, Query(ge=0)] = None,
    score_min: Annotated[int | None, Query(ge=1, le=100)] = None,
    score_max: Annotated[int | None, Query(ge=1, le=100)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> CustomerList:
    _validate_range(age_min, age_max, "age_min", "age_max")
    _validate_range(income_min, income_max, "income_min", "income_max")
    _validate_range(score_min, score_max, "score_min", "score_max")

    clauses: list[str] = []
    parameters: list[object] = []
    for value, column, operator in (
        (gender.value if gender else None, "gender", "="),
        (age_min, "age", ">="),
        (age_max, "age", "<="),
        (income_min, "annual_income_kusd", ">="),
        (income_max, "annual_income_kusd", "<="),
        (score_min, "spending_score", ">="),
        (score_max, "spending_score", "<="),
    ):
        if value is not None:
            clauses.append(f"{column} {operator} ?")
            parameters.append(value)

    if q is not None:
        search_value = q.strip()
        if not search_value:
            raise HTTPException(status_code=422, detail="q cannot be blank.")
        search_pattern = _literal_search_pattern(search_value)
        clauses.append(
            "(" + " OR ".join(
                f"CAST({column} AS TEXT) LIKE ? ESCAPE '\\'"
                for column in (
                    "customer_id",
                    "gender",
                    "age",
                    "annual_income_kusd",
                    "spending_score",
                )
            ) + ")"
        )
        parameters.extend([search_pattern] * 5)

    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    offset = (page - 1) * page_size

    with open_database() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM customers{where_clause}",  # noqa: S608
            parameters,
        ).fetchone()[0]
        rows = connection.execute(
            """
            SELECT customer_id, gender, age, annual_income_kusd, spending_score
            FROM customers
            """
            + where_clause
            + " ORDER BY customer_id ASC LIMIT ? OFFSET ?",
            [*parameters, page_size, offset],
        ).fetchall()

    total_pages = (total + page_size - 1) // page_size if total else 0
    return CustomerList(
        items=[_customer_from_row(row) for row in rows],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
    )


@app.get("/api/v1/customers/{customer_id}", response_model=Customer, tags=["customers"])
def get_customer(
    customer_id: Annotated[str, Path(pattern=r"^\d{4}$")],
) -> Customer:
    with open_database() as connection:
        row = connection.execute(
            """
            SELECT customer_id, gender, age, annual_income_kusd, spending_score
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return _customer_from_row(row)
