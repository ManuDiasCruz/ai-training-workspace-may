"""Uniform error responses.

Every failure leaves the API in the same envelope, so a client can parse one
shape regardless of whether a request was rejected by validation, missed a
record, or hit an unavailable database:

    {"error": {"code": "not_found", "message": "...", "details": [...]}}
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db import DatabaseNotReady

logger = logging.getLogger("shopapi")

# Machine-readable code per status, so clients can branch without parsing prose.
_CODE_BY_STATUS = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_error",
    status.HTTP_503_SERVICE_UNAVAILABLE: "database_unavailable",
}


def error_response(
    status_code: int,
    message: str,
    *,
    code: str | None = None,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "code": code or _CODE_BY_STATUS.get(status_code, "error"),
        "message": message,
    }
    if details:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content={"error": payload})


def _format_location(location: tuple[Any, ...]) -> str:
    """Turn Pydantic's loc tuple into a caller-facing field name.

    The first element is the request part ("query", "path", "body"), which is
    noise to someone who only wants to know which parameter to fix.
    """
    parts = [str(part) for part in location]
    if parts and parts[0] in {"query", "path", "body", "header", "cookie"}:
        parts = parts[1:]
    return ".".join(parts) or "request"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": _format_location(err.get("loc", ())), "message": err.get("msg", "invalid value")}
            for err in exc.errors()
        ]
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "One or more request parameters are invalid.",
            details=details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(DatabaseNotReady)
    async def _db_not_ready(_: Request, exc: DatabaseNotReady) -> JSONResponse:
        # Expected during first-time setup, so it is a plain warning with an
        # actionable message rather than a stack trace.
        logger.warning("Database not ready: %s", exc)
        return error_response(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

    @app.exception_handler(sqlite3.Error)
    async def _sqlite_error(_: Request, exc: sqlite3.Error) -> JSONResponse:
        # Log the driver message; return a generic one. SQLite errors can
        # contain schema and filesystem details that clients need not see.
        logger.exception("Database error: %s", exc)
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "A database error occurred while handling the request.",
            code="database_error",
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred."
        )
