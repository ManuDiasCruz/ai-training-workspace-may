"""Customer listing and retrieval endpoints."""

from __future__ import annotations

import math
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app import repository
from app.db import get_connection
from app.models import Customer, CustomerPage, CustomerQuery, Pagination

router = APIRouter(prefix="/api/v1", tags=["customers"])

Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get(
    "/customers",
    response_model=CustomerPage,
    summary="List customers with pagination, filtering, search and sorting",
    responses={
        422: {"description": "Invalid or unknown query parameter."},
        503: {"description": "Database has not been created yet."},
    },
)
def list_customers(
    conn: Connection,
    query: Annotated[CustomerQuery, Query()],
) -> CustomerPage:
    """Return one page of customers.

    Filters combine with AND. `total_items` counts everything matching the
    filters, not just the current page, so a client can size a pager before
    walking it.
    """
    total_items = repository.count_customers(conn, query)
    rows = repository.list_customers(conn, query)

    total_pages = math.ceil(total_items / query.page_size) if total_items else 0

    return CustomerPage(
        items=[Customer(**dict(row)) for row in rows],
        pagination=Pagination(
            page=query.page,
            page_size=query.page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=query.page < total_pages,
            has_previous=query.page > 1 and total_items > 0,
        ),
    )


@router.get(
    "/customers/{customer_id}",
    response_model=Customer,
    summary="Fetch a single customer by identifier",
    responses={
        404: {"description": "No customer with that identifier."},
        422: {"description": "Identifier is not 1-4 digits."},
        503: {"description": "Database has not been created yet."},
    },
)
def get_customer(
    conn: Connection,
    customer_id: Annotated[
        str,
        Path(
            # Rejects non-numeric input at the edge, so a bad identifier is a
            # 422 about its format rather than a 404 implying it might exist.
            pattern=r"^\d{1,4}$",
            description="Dataset identifier. Accepted with or without zero padding ('7' or '0007').",
            examples=["0001"],
        ),
    ],
) -> Customer:
    row = repository.get_customer(conn, customer_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No customer with id '{customer_id.zfill(4)}'.",
        )
    return Customer(**dict(row))
