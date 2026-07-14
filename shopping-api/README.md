# Shopping API

A small production-style REST API built on top of the mall customers shopping
dataset (`Shopping_data.csv`, 200 records). The dataset is imported into a
local SQLite database and exposed through a FastAPI application with
pagination, filtering, search, aggregate statistics, input validation and
automated tests.

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 · SQLite · pytest

## Dataset

Source: `data/Shopping_data.csv` (downloaded from Google Drive). Columns:

| CSV column               | Type    | Description                    |
|--------------------------|---------|--------------------------------|
| `CustomerID`             | int     | Unique customer id (1–200)     |
| `Genre`                  | text    | `Male` or `Female`             |
| `Age`                    | int     | Customer age                   |
| `Annual Income (k$)`     | int     | Annual income in thousands USD |
| `Spending Score (1-100)` | int     | Mall-assigned spending score   |

## Database design

Single table, since the dataset is a flat list of independent records:

```sql
CREATE TABLE customers (
    id              INTEGER PRIMARY KEY,          -- CustomerID
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age > 0),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
CREATE INDEX ix_customers_genre           ON customers (genre);
CREATE INDEX ix_customers_annual_income_k ON customers (annual_income_k);
CREATE INDEX ix_customers_spending_score  ON customers (spending_score);
```

Design notes:

- `CustomerID` is reused as the primary key, which makes the import idempotent
  (rows are upserted by id — re-running the import never duplicates data).
- CHECK constraints enforce data sanity at the database level; the import
  script additionally validates every row and reports skipped ones.
- Indexes cover the filterable columns.
- The database file defaults to `shopping.db` in this directory and can be
  redirected with the `SHOPPING_API_DB` environment variable (used by tests).

## Project layout

```
shopping-api/
├── app/
│   ├── database.py     # engine, session factory, FastAPI dependency
│   ├── models.py       # SQLAlchemy ORM model (customers table)
│   ├── schemas.py      # Pydantic response schemas
│   └── main.py         # FastAPI app and endpoints
├── data/
│   └── Shopping_data.csv
├── scripts/
│   └── import_data.py  # CSV -> SQLite import (idempotent, validating)
├── tests/
│   └── test_api.py     # automated API tests (pytest)
└── requirements.txt
```

## Setup

From the `shopping-api/` directory:

```bash
# 1. (Optional) create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Import the dataset into SQLite (creates shopping.db)
python scripts/import_data.py
```

## Running the API

```bash
uvicorn app.main:app --reload
```

The API is then available at `http://127.0.0.1:8000`, with interactive
OpenAPI docs at `http://127.0.0.1:8000/docs`.

## Running the tests

```bash
python -m pytest tests/ -v
```

The test suite seeds a throwaway SQLite database from the real CSV and covers
pagination, filtering, sorting, search, error handling (400/404/422) and the
stats endpoint (13 tests).

## API reference

| Method | Path                | Description                                  |
|--------|---------------------|----------------------------------------------|
| GET    | `/health`           | Liveness check + row count                   |
| GET    | `/customers`        | List customers (pagination/filtering/sorting)|
| GET    | `/customers/{id}`   | Fetch a single customer by id                |
| GET    | `/customers/search` | Basic search across fields                   |
| GET    | `/stats`            | Aggregate statistics (overall and per genre) |

### `GET /customers` query parameters

| Parameter    | Type | Constraints              | Description                        |
|--------------|------|--------------------------|------------------------------------|
| `page`       | int  | ≥ 1 (default 1)          | 1-based page number                |
| `page_size`  | int  | 1–100 (default 20)       | Items per page                     |
| `genre`      | enum | `Male` / `Female`        | Filter by genre                    |
| `min_age`    | int  | 1–120                    | Minimum age (inclusive)            |
| `max_age`    | int  | 1–120                    | Maximum age (inclusive)            |
| `min_income` | int  | ≥ 0                      | Minimum annual income (k$)         |
| `max_income` | int  | ≥ 0                      | Maximum annual income (k$)         |
| `min_score`  | int  | 1–100                    | Minimum spending score             |
| `max_score`  | int  | 1–100                    | Maximum spending score             |
| `sort_by`    | enum | `id`, `age`, `annual_income_k`, `spending_score` | Sort column |
| `order`      | enum | `asc` / `desc`           | Sort direction                     |

An inverted range (e.g. `min_age=50&max_age=20`) returns **400**; type or
bound violations return **422** (FastAPI validation); an unknown customer id
returns **404**.

### Examples

```bash
# Second page, 5 per page
curl "http://127.0.0.1:8000/customers?page=2&page_size=5"

# Female customers aged 30-40 earning at least 60k, highest spenders first
curl "http://127.0.0.1:8000/customers?genre=Female&min_age=30&max_age=40&min_income=60&sort_by=spending_score&order=desc"

# Single customer
curl "http://127.0.0.1:8000/customers/42"

# Search: text matches genre, numbers match id/age/income/score
curl "http://127.0.0.1:8000/customers/search?q=female"
curl "http://127.0.0.1:8000/customers/search?q=137"

# Aggregate statistics
curl "http://127.0.0.1:8000/stats"
```

Example `/customers` response:

```json
{
  "items": [
    {"id": 8, "genre": "Female", "age": 23, "annual_income_k": 18, "spending_score": 94}
  ],
  "total": 112,
  "page": 2,
  "page_size": 3,
  "pages": 38
}
```

## Known limitations & future improvements

- **Read-only API** — no POST/PUT/DELETE endpoints; the dataset is only
  written by the import script.
- **SQLite** — perfect for a local dataset of this size, but a client/server
  database (PostgreSQL) plus migrations (Alembic) would be the next step for
  real deployments.
- **No authentication or rate limiting** — all endpoints are public.
- **Basic search only** — matches genre text and exact numeric values; no
  fuzzy matching or multi-term queries.
- **No CI pipeline** — tests run locally; a GitHub Actions workflow would run
  them on every push.
- **No containerization** — a Dockerfile/compose setup would make the local
  setup one command.
