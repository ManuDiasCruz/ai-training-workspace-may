
from __future__ import annotations

import math
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated, Iterator, Literal

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

from .database import connect, seed_if_empty


class Customer(BaseModel):
    customer_id: str = Field(examples=["0001"])
    gender: Literal["Male", "Female"]
    age: int
    annual_income_kusd: int
    spending_score: int


class CustomerPage(BaseModel):
    items: list[Customer]
    page: int
    page_size: int
    total: int
    pages: int


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_if_empty()
    yield


app = FastAPI(
    title="Shopping Customer API",
    version="1.0.0",
    description="Read-only access to the persisted shopping customer dataset.",
    lifespan=lifespan,
)


def get_connection() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()


Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@app.get("/health", tags=["system"])
def health(connection: Connection) -> dict[str, int | str]:
    count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    return {"status": "ok", "records": count}


@app.get("/customers", response_model=CustomerPage, tags=["customers"])
def list_customers(
    connection: Connection,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    gender: Annotated[Literal["Male", "Female"] | None, Query()] = None,
    age_min: Annotated[int | None, Query(ge=0, le=120)] = None,
    age_max: Annotated[int | None, Query(ge=0, le=120)] = None,
    income_min: Annotated[int | None, Query(ge=0)] = None,
    income_max: Annotated[int | None, Query(ge=0)] = None,
    score_min: Annotated[int | None, Query(ge=1, le=100)] = None,
    score_max: Annotated[int | None, Query(ge=1, le=100)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
) -> CustomerPage:
    ranges = (
        (age_min, age_max, "age"),
        (income_min, income_max, "income"),
        (score_min, score_max, "score"),
    )
    for lower, upper, label in ranges:
        if lower is not None and upper is not None and lower > upper:
            raise HTTPException(422, f"{label}_min cannot be greater than {label}_max")

    clauses: list[str] = []
    values: list[object] = []
    filters = (
        (gender, "gender = ?"),
        (age_min, "age >= ?"),
        (age_max, "age <= ?"),
        (income_min, "annual_income_kusd >= ?"),
        (income_max, "annual_income_kusd <= ?"),
        (score_min, "spending_score >= ?"),
        (score_max, "spending_score <= ?"),
    )
    for value, clause in filters:
        if value is not None:
            clauses.append(clause)
            values.append(value)
    if q is not None:
        clauses.append("(customer_id LIKE ? COLLATE NOCASE OR gender LIKE ? COLLATE NOCASE)")
        term = f"%{q.strip()}%"
        values.extend([term, term])

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    total = connection.execute(
        f"SELECT COUNT(*) FROM customers{where}", values
    ).fetchone()[0]
    rows = connection.execute(
        f"""
        SELECT customer_id, gender, age, annual_income_kusd, spending_score
        FROM customers{where}
        ORDER BY customer_id
        LIMIT ? OFFSET ?
        """,
        [*values, page_size, (page - 1) * page_size],
    ).fetchall()
    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size),
    )


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"])
def get_customer(
    connection: Connection,
    customer_id: Annotated[str, Path(pattern=r"^\d{4}$")],
) -> Customer:
    row = connection.execute(
        """
        SELECT customer_id, gender, age, annual_income_kusd, spending_score
        FROM customers WHERE customer_id = ?
        """,
        (customer_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "Customer not found")
    return Customer(**dict(row))

