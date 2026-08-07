"""Health and dataset-statistics endpoints."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app import __version__, config, db, repository
from app.db import get_connection
from app.models import DatasetStats, HealthStatus

router = APIRouter(tags=["meta"])

Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("/health", response_model=HealthStatus, summary="Liveness and database readiness")
def health() -> HealthStatus:
    """Report service and database state.

    Deliberately does not depend on get_connection: a health check has to be
    able to *report* an unavailable database, which it cannot do if a missing
    database makes the endpoint itself fail.
    """
    path = config.db_path()
    if not path.exists():
        return HealthStatus(
            status="degraded", database="missing", customer_count=0, version=__version__
        )

    conn = db.connect(path)
    try:
        if not db.customers_table_exists(conn):
            return HealthStatus(
                status="degraded",
                database="schema_missing",
                customer_count=0,
                version=__version__,
            )
        count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    except sqlite3.Error:
        return HealthStatus(
            status="degraded", database="error", customer_count=0, version=__version__
        )
    finally:
        conn.close()

    # A reachable but empty table is not healthy: the API would serve empty
    # pages that look like legitimate results.
    return HealthStatus(
        status="ok" if count > 0 else "degraded",
        database="ready" if count > 0 else "empty",
        customer_count=count,
        version=__version__,
    )


@router.get(
    "/api/v1/stats",
    response_model=DatasetStats,
    tags=["customers"],
    summary="Aggregate statistics for the whole dataset",
    responses={503: {"description": "Database has not been created yet."}},
)
def stats(conn: Connection) -> DatasetStats:
    """Dataset-wide totals, per-genre breakdown, numeric ranges and spending
    bands, plus the provenance of the current import."""
    return DatasetStats(**repository.dataset_stats(conn))
