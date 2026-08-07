"""ShopAPI application entry point.

Run locally with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app import __version__, config
from app.errors import register_error_handlers
from app.routers import customers, meta

logger = logging.getLogger("shopapi")

DESCRIPTION = """
Read-only REST API over the shopping dataset (200 mall customers).

**Endpoints**

* `GET /health` — service and database readiness
* `GET /api/v1/customers` — list with pagination, filtering, search and sorting
* `GET /api/v1/customers/{customer_id}` — fetch one record
* `GET /api/v1/stats` — aggregate statistics and import provenance

The dataset is a fixed snapshot imported from CSV, so the API exposes no
write operations. Populate the database before starting the server:

```
python -m scripts.import_dataset
```
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Surface a missing database at boot rather than leaving the first caller
    # to discover it. Not fatal: /health is designed to report exactly this,
    # and the server should stay up to say so.
    path = config.db_path()
    if path.exists():
        logger.info("Using database at %s", path)
    else:
        logger.warning(
            "Database not found at %s -- run 'python -m scripts.import_dataset' "
            "to create it. Data endpoints will return 503 until then.",
            path,
        )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ShopAPI",
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_error_handlers(app)
    app.include_router(meta.router)
    app.include_router(customers.router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return app


app = create_app()
