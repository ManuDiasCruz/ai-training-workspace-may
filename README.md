# Shopping Customers API

A small, production-style REST API over the **Mall Customer Segmentation**
shopping dataset. It loads the dataset from a CSV into a local SQLite database
and exposes it through a versioned HTTP API built with **FastAPI** and
**SQLAlchemy**, with pagination, filtering, search, summary statistics,
input validation, structured error handling and an automated test suite.

> Branch: `claude-efa01d4a-shopping-api`

---

## Table of contents

- [Project description](#project-description)
- [Dataset](#dataset)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Database design](#database-design)
- [Setup](#setup)
- [Execution](#execution)
- [API reference](#api-reference)
- [API usage examples](#api-usage-examples)
- [Running the tests](#running-the-tests)
- [Configuration](#configuration)
- [Known limitations & future improvements](#known-limitations--future-improvements)

---

## Project description

The service answers practical questions about a mall's customer base, e.g.
*"list female customers aged 30–35"*, *"who are the top spenders earning over
70k?"*, or *"what is the average spending score by gender?"*. It is intentionally
small but follows a clean, layered structure (config → database → models →
import → query layer → API) so it can be read end-to-end and extended easily.

Key features:

- **Persistent local database** – the CSV is imported into SQLite via an
  idempotent, validated import step.
- **Listing + pagination** – page/page-size based, with full pagination metadata.
- **Filtering** – by gender and by inclusive ranges on age, annual income and
  spending score.
- **Search** – a basic free-text `search` parameter.
- **Sorting** – by any numeric field, ascending or descending.
- **Summary statistics** – counts, gender distribution and min/max/average of
  every numeric field, honouring the same filters.
- **Validation & error handling** – query constraints, cross-field range checks
  and a consistent JSON error envelope.
- **Interactive docs** – auto-generated OpenAPI/Swagger UI at `/docs`.

## Dataset

`data/Shopping_data.csv` – 200 customer records, one header row, comma-separated.

| Column                   | Example | Notes                                  |
| ------------------------ | ------- | -------------------------------------- |
| `CustomerID`             | `0001`  | Sequential ID, zero-padded in the CSV  |
| `Genre`                  | `Male`  | Gender (`Male` / `Female`)             |
| `Age`                    | `19`    | Years                                  |
| `Annual Income (k$)`     | `15`    | Thousands of US dollars                |
| `Spending Score (1-100)` | `39`    | Mall-assigned score, 1–100             |

Quick profile of the data: **200 customers** (112 Female / 88 Male), ages
**18–70**, annual income **15–137 k\$**, spending score **1–99**.

## Tech stack

- **Python 3.10+**
- **FastAPI** – web framework + request validation
- **SQLAlchemy 2.0** – ORM / database access
- **Pydantic 2** – response models & validation
- **SQLite** – zero-config local database
- **Uvicorn** – ASGI server
- **pytest** + **httpx** – automated tests

## Project structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py        # env-overridable settings (paths, DB URL, metadata)
│   ├── database.py      # engine, session factory, declarative Base, get_db()
│   ├── models.py        # SQLAlchemy Customer model + indexes
│   ├── schemas.py       # Pydantic request/response models & enums
│   ├── crud.py          # read queries: list, get, stats (filter/sort logic)
│   ├── seed.py          # validated CSV importer
│   └── main.py          # FastAPI app, routes, error handlers, startup
├── data/
│   └── Shopping_data.csv
├── scripts/
│   └── init_db.py       # CLI to create the schema and seed the database
├── tests/
│   ├── conftest.py      # temp DB + TestClient fixtures
│   └── test_api.py      # 20 API tests
├── requirements.txt
├── pytest.ini
└── README.md
```

## Database design

The dataset is a single flat table of independent customer records, so a
**single normalised table** is the appropriate design. The CSV headers are
mapped onto clean, snake_case attributes:

| CSV column               | Column            | Type          | Constraints          |
| ------------------------ | ----------------- | ------------- | -------------------- |
| `CustomerID`             | `customer_id`     | `INTEGER`     | **Primary key**      |
| `Genre`                  | `gender`          | `VARCHAR(10)` | `NOT NULL`, indexed  |
| `Age`                    | `age`             | `INTEGER`     | `NOT NULL`, indexed  |
| `Annual Income (k$)`     | `annual_income_k` | `INTEGER`     | `NOT NULL`, indexed  |
| `Spending Score (1-100)` | `spending_score`  | `INTEGER`     | `NOT NULL`, indexed  |

**Design decisions**

- **`customer_id` as primary key.** `CustomerID` is already a stable, unique
  identifier in the source data, so it is used directly as the natural key. It
  is stored as `INTEGER`, which drops the cosmetic leading zeros (`0001` → `1`).
- **`Genre` → `gender`.** The source column is renamed to reflect its actual
  meaning. Values are stored verbatim (`Male` / `Female`).
- **Indexes on every filterable column** (`gender`, `age`, `annual_income_k`,
  `spending_score`) keep equality and range queries efficient as the dataset
  grows. The dataset is tiny today, but indexing demonstrates the intended
  production behaviour.
- **Typed, `NOT NULL` numeric columns.** All numeric fields are integers and
  required; the importer rejects malformed rows rather than inserting nulls.

The schema is created from the SQLAlchemy model (`Base.metadata.create_all`), so
the model in `app/models.py` is the single source of truth.

## Setup

Requires Python 3.10+.

```bash
# 1. Clone and switch to this branch
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git checkout claude-efa01d4a-shopping-api

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Execution

```bash
# 1. Create the SQLite database and import the dataset (200 records)
python -m scripts.init_db

# 2. Run the API
uvicorn app.main:app --reload
#   (equivalently: python -m uvicorn app.main:app --reload)
```

The API is then available at **http://127.0.0.1:8000**:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>
- Health check: <http://127.0.0.1:8000/health>

> **Note:** step 1 is optional — on startup the app automatically creates the
> schema and seeds an empty database from the CSV (`SHOPPING_AUTO_SEED=true` by
> default). Running `init_db` explicitly is recommended so the import is a
> deliberate, observable step.

## API reference

| Method | Path                          | Description                                            |
| ------ | ----------------------------- | ------------------------------------------------------ |
| GET    | `/health`                     | Liveness check + number of customers loaded            |
| GET    | `/api/v1/customers`           | List customers (pagination, filtering, search, sort)   |
| GET    | `/api/v1/customers/{id}`      | Retrieve a single customer by ID                       |
| GET    | `/api/v1/stats`               | Aggregate statistics (accepts the same filters)        |

### Query parameters for `/api/v1/customers` and `/api/v1/stats`

| Parameter            | Type   | Default       | Constraints / notes                                   |
| -------------------- | ------ | ------------- | ----------------------------------------------------- |
| `page`               | int    | `1`           | `>= 1` (list only)                                    |
| `page_size`          | int    | `20`          | `1`–`100` (list only)                                 |
| `gender`             | enum   | –             | `Male` or `Female`                                    |
| `min_age`            | int    | –             | `0`–`120`                                             |
| `max_age`            | int    | –             | `0`–`120`, must be `>= min_age`                       |
| `min_income`         | int    | –             | `>= 0` (k\$)                                          |
| `max_income`         | int    | –             | `>= 0`, must be `>= min_income`                       |
| `min_spending_score` | int    | –             | `1`–`100`                                             |
| `max_spending_score` | int    | –             | `1`–`100`, must be `>= min_spending_score`            |
| `search`             | string | –             | Case-insensitive gender match, or exact ID if numeric |
| `sort_by`            | enum   | `customer_id` | `customer_id` \| `age` \| `annual_income_k` \| `spending_score` (list only) |
| `order`              | enum   | `asc`         | `asc` \| `desc` (list only)                           |

**Search semantics.** Because the dataset has no free-text columns, `search` is
deliberately scoped: it matches a customer's `gender` (case-insensitive) and, if
the term is numeric, an exact `customer_id`. For example `search=female` returns
all female customers and `search=42` returns customer 42.

### Error format

All 4xx/5xx responses share one envelope:

```json
{ "error": { "status": 422, "message": "…", "details": [ … ] } }
```

`details` is present only for request-validation (422) errors.

## API usage examples

> The examples below are real responses from the running service (trimmed for
> brevity).

**List with pagination**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?page=1&page_size=3"
```

```json
{
  "data": [
    { "customer_id": 1, "gender": "Male", "age": 19, "annual_income_k": 15, "spending_score": 39 },
    { "customer_id": 2, "gender": "Male", "age": 21, "annual_income_k": 15, "spending_score": 81 },
    { "customer_id": 3, "gender": "Female", "age": 20, "annual_income_k": 16, "spending_score": 6 }
  ],
  "pagination": {
    "page": 1, "page_size": 3, "total_items": 200,
    "total_pages": 67, "has_next": true, "has_previous": false
  }
}
```

**Filter (female, aged 30–35)**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?gender=Female&min_age=30&max_age=35&page_size=3"
# -> total_items: 28
```

**Top spenders earning over 70k (filter + sort)**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?min_income=70&sort_by=spending_score&order=desc&page_size=3"
```

```json
{
  "data": [
    { "customer_id": 186, "gender": "Male",   "age": 30, "annual_income_k": 99, "spending_score": 97 },
    { "customer_id": 146, "gender": "Male",   "age": 28, "annual_income_k": 77, "spending_score": 97 },
    { "customer_id": 168, "gender": "Female", "age": 33, "annual_income_k": 86, "spending_score": 95 }
  ],
  "pagination": { "page": 1, "page_size": 3, "total_items": 76, "total_pages": 26, "has_next": true, "has_previous": false }
}
```

**Search**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?search=42"      # customer 42
curl "http://127.0.0.1:8000/api/v1/customers?search=female"  # all 112 female customers
```

**Get a single customer**

```bash
curl "http://127.0.0.1:8000/api/v1/customers/42"
# { "customer_id": 42, "gender": "Male", "age": 24, "annual_income_k": 38, "spending_score": 92 }
```

**Not found (404)**

```bash
curl "http://127.0.0.1:8000/api/v1/customers/99999"
# { "error": { "status": 404, "message": "Customer with id 99999 not found." } }
```

**Validation error (422)**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?min_age=40&max_age=20"
# { "error": { "status": 422, "message": "min_age (40) must be less than or equal to max_age (20)." } }
```

**Summary statistics**

```bash
curl "http://127.0.0.1:8000/api/v1/stats"
```

```json
{
  "total_customers": 200,
  "gender_distribution": { "Male": 88, "Female": 112 },
  "age": { "min": 18, "max": 70, "average": 38.85 },
  "annual_income_k": { "min": 15, "max": 137, "average": 60.56 },
  "spending_score": { "min": 1, "max": 99, "average": 50.2 },
  "filters_applied": {}
}
```

`/api/v1/stats` accepts the same filters, e.g. `?gender=Male` returns statistics
for the 88 male customers only.

## Running the tests

```bash
pytest
```

The suite (20 tests) spins up the app against an **isolated temporary SQLite
database** seeded from the bundled CSV, and covers health, listing, pagination,
filtering, search, sorting, single-record retrieval (found + 404), validation
errors and statistics. It does not touch your local `shopping.db`.

## Configuration

All settings are environment variables (see `app/config.py`):

| Variable                | Default                       | Purpose                                         |
| ----------------------- | ----------------------------- | ----------------------------------------------- |
| `SHOPPING_DATABASE_URL` | `sqlite:///./shopping.db`     | SQLAlchemy database URL                         |
| `SHOPPING_DATASET_PATH` | `data/Shopping_data.csv`      | Path to the dataset CSV used by the importer    |
| `SHOPPING_AUTO_SEED`    | `true`                        | Seed an empty database automatically on startup |

## Known limitations & future improvements

- **Read-only API.** Only `GET` endpoints are implemented; there is no
  create/update/delete. *Future:* add authenticated write endpoints with
  optimistic concurrency.
- **Single-process SQLite.** Great for local use, but not for concurrent
  writes/horizontal scaling. *Future:* support PostgreSQL via the existing
  `DATABASE_URL` config and add Alembic migrations.
- **Basic search.** The dataset has no rich text fields, so `search` only covers
  gender and customer ID. *Future:* add full-text search if/when textual columns
  (e.g. product/category names) are introduced.
- **No customer segmentation.** This is the classic clustering dataset, but no
  segmentation/analytics endpoints are exposed. *Future:* add K-Means-based
  spending segments and a `/segments` endpoint.
- **No auth / rate limiting.** The API is open. *Future:* add API keys/OAuth and
  request throttling for production exposure.
- **No containerisation/CI.** *Future:* add a `Dockerfile`, `docker-compose` and
  a GitHub Actions workflow running `pytest` on every push.
- **Offset pagination.** Fine at this scale; *future:* cursor/keyset pagination
  for large datasets.

These items are tracked as GitHub issues on the repository, each referencing this
branch.
