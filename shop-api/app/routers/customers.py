"""Dataset endpoints."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from .. import repository
from ..db import get_connection
from ..models import (
    Customer,
    CustomerListQuery,
    CustomerPage,
    ErrorResponse,
    PageMeta,
    StatsResponse,
)

router = APIRouter(tags=["customers"])

Conn = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get(
    "/customers",
    response_model=CustomerPage,
    summary="List customers with pagination, filtering and search",
    responses={422: {"model": ErrorResponse, "description": "Invalid query parameters"}},
)
def list_customers(
    conn: Conn,
    query: Annotated[CustomerListQuery, Query()],
) -> CustomerPage:
    """Return a page of customer records.

    Filters combine with AND. `q` searches the customer id and gender label.
    """
    total_items = repository.count_customers(conn, query)
    rows = repository.list_customers(conn, query)

    total_pages = -(-total_items // query.page_size) if total_items else 0
    meta = PageMeta(
        page=query.page,
        page_size=query.page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=query.page < total_pages,
        has_prev=query.page > 1 and total_items > 0,
    )
    return CustomerPage(meta=meta, data=[Customer(**row) for row in rows])


@router.get(
    "/customers/{customer_id}",
    response_model=Customer,
    summary="Fetch a single customer by id",
    responses={
        404: {"model": ErrorResponse, "description": "No such customer"},
        422: {"model": ErrorResponse, "description": "Malformed id"},
    },
)
def get_customer(
    conn: Conn,
    customer_id: Annotated[
        str,
        Path(
            pattern=r"^\d{1,4}$",
            description="Customer id, zero-padded or not: '0001' and '1' both work",
            examples=["0001"],
        ),
    ],
) -> Customer:
    numeric_id = int(customer_id)
    row = repository.get_customer(conn, numeric_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No customer with id '{customer_id}'.",
        )
    return Customer(**row)


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Aggregate statistics for the whole dataset",
)
def get_stats(conn: Conn) -> StatsResponse:
    return StatsResponse(**repository.stats(conn))
