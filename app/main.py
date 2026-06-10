"""Application entry point for the Shopping Customers API.

Run locally with::

    uvicorn app.main:app --reload

Interactive docs are served at http://127.0.0.1:8000/docs once running.
"""

from __future__ import annotations

import sqlite3

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .database import get_db_path
from .routes import router

DESCRIPTION = """
REST API over the mall shopping customers dataset (200 customers with
genre, age, annual income and spending score).

Build the database first with `python -m scripts.import_data`.
"""


def _error_response(status_code: int, message: str, details: list | None = None) -> JSONResponse:
    body: dict = {"error": {"code": status_code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Shopping Customers API",
        version="1.0.0",
        description=DESCRIPTION,
    )
    app.include_router(router)

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    def health() -> dict:
        db_path = get_db_path()
        return {"status": "ok", "database": str(db_path), "database_ready": db_path.exists()}

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(422, "Validation failed", details=jsonable_encoder(exc.errors()))

    @app.exception_handler(sqlite3.Error)
    async def sqlite_error_handler(request: Request, exc: sqlite3.Error) -> JSONResponse:
        # Most likely cause: the database has not been built yet.
        return _error_response(
            500,
            "Database error. If the database has not been created yet, run "
            "'python -m scripts.import_data' from the repository root.",
        )

    return app


app = create_app()
