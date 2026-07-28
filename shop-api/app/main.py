"""FastAPI application for the shopping dataset.

Read-only HTTP interface over the imported Mall Customers dataset. Every error
response uses the ErrorResponse envelope defined in models.py.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config, db, repository
from .models import ErrorBody, ErrorDetail, ErrorResponse, HealthResponse
from .routers import customers

app = FastAPI(
    title="Shop API",
    version="1.0.0",
    summary="REST API over the Mall Customers shopping dataset.",
    description=(
        "Read-only access to 200 shopping records with pagination, filtering, "
        "search and aggregate statistics.\n\n"
        "Interactive docs: `/docs` - OpenAPI schema: `/openapi.json`"
    ),
)

# Status codes mapped to stable, machine-readable error codes so clients can
# branch on `error.code` instead of parsing prose.
_ERROR_CODES = {
    400: "bad_request",
    404: "not_found",
    422: "validation_error",
    500: "internal_error",
    503: "service_unavailable",
}


def _error_response(status_code: int, message: str, details=None) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=_ERROR_CODES.get(status_code, "error"),
            message=message,
            details=details,
        )
    )
    return JSONResponse(
        status_code=status_code, content=body.model_dump(exclude_none=True)
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _error_response(exc.status_code, detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = []
    for error in exc.errors():
        # loc is like ('query', 'page_size'); drop the leading source segment so
        # the client sees the parameter name it actually sent. A cross-field rule
        # fails with loc ('query',) alone, which leaves no field to point at --
        # those are reported with the message only.
        location = ".".join(str(part) for part in error["loc"][1:])
        message = error["msg"].removeprefix("Value error, ")
        details.append(ErrorDetail(field=location or None, message=message))
    return _error_response(
        422, "One or more request parameters are invalid.", details
    )


@app.exception_handler(db.DatabaseNotInitialized)
async def database_missing_handler(
    request: Request, exc: db.DatabaseNotInitialized
) -> JSONResponse:
    # 503 rather than 500: the service is fine, the dataset just is not loaded,
    # and the message says exactly how to fix it.
    return _error_response(503, str(exc))


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Liveness probe that also reports what dataset is loaded."""
    conn = db.connect(read_only=True)
    try:
        count = repository.record_count(conn)
        meta = repository.import_metadata(conn) or {}
    finally:
        conn.close()
    return HealthResponse(
        status="ok",
        database=str(config.db_path()),
        record_count=count,
        source_file=meta.get("source_file"),
        imported_at=meta.get("imported_at"),
    )


app.include_router(customers.router, prefix=config.API_PREFIX)
