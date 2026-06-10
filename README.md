# Shopping Customers API

A small production-style REST API over the mall **shopping customers dataset**
(`data/Shopping_data.csv`, sourced from Google Drive): 200 customers described
by genre, age, annual income and spending score. The dataset is persisted into
a local SQLite database and exposed through a FastAPI service with listing,
pagination, filtering, search, sorting and aggregate statistics.

> Branch: `fable-efa01d4a-shopping-api`

## Dataset

| CSV column               | Type    | Notes                                  |
|--------------------------|---------|----------------------------------------|
| `CustomerID`             | int     | Zero-padded in the CSV (`0001`–`0200`) |
| `Genre`                  | text    | `Male` / `Female` (dataset's own label for gender) |
| `Age`                    | int     | 18–70 in this data                     |
| `Annual Income (k$)`     | int     | Thousands of dollars, 15–137           |
| `Spending Score (1-100)` | int     | Store-assigned score, 1–99             |

The CSV is kept byte-identical to the Drive original (CRLF line endings,
enforced via `.gitattributes`). The dataset's `Genre` naming is preserved
throughout the API for traceability back to the source columns.

## Database design

A single SQLite table — the dataset is one flat entity, so one table is the
honest design (no joins to invent). IDs are stored as plain integers; the
zero-padded display form is reconstructed for search.

```sql
CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX idx_customers_genre  ON customers (genre);
CREATE INDEX idx_customers_age    ON customers (age);
CREATE INDEX idx_customers_income ON customers (annual_income_k);
CREATE INDEX idx_customers_score  ON customers (spending_score);
```

- **CHECK constraints** enforce data integrity at the storage layer, mirroring
  the validation done at import time and at the API boundary.
- **Indexes** cover every filterable/sortable column.
- The database file (`data/shopping.db`) is disposable and git-ignored: it is
  rebuilt from the CSV by the import script, which validates every row first
  and writes in a single all-or-nothing transaction (idempotent — re-running
  never duplicates rows).

## Project structure

```
app/
  main.py        # FastAPI app factory + global error handlers
  routes.py      # endpoint definitions and query-parameter validation
  repository.py  # all SQL (parameterized; sort fields whitelisted)
  schemas.py     # Pydantic response models
  database.py    # SQLite connection helpers + schema DDL
scripts/
  import_data.py # CSV -> SQLite import pipeline (validating, idempotent)
data/
  Shopping_data.csv
tests/
  conftest.py    # builds a throwaway DB from the real CSV
  test_api.py    # 21 end-to-end API tests
```

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
# 1. Build the database from the CSV (idempotent, safe to re-run)
python -m scripts.import_data
# -> Imported 200 customers from data/Shopping_data.csv into data/shopping.db

# 2. Start the API
uvicorn app.main:app --reload
```

Interactive OpenAPI docs: <http://127.0.0.1:8000/docs>.
The database location can be overridden with the `SHOPPING_DB_PATH`
environment variable (used by the test suite).

## Running the tests

```bash
pytest
# 21 passed
```

The suite imports the real CSV into a temporary database and exercises the
API end to end: pagination math, every filter, search semantics, sorting,
validation failures and error envelopes.

## API reference

| Method | Path                         | Description                                  |
|--------|------------------------------|----------------------------------------------|
| GET    | `/health`                    | Liveness probe + database readiness          |
| GET    | `/api/v1/customers`          | List customers (pagination/filter/search/sort) |
| GET    | `/api/v1/customers/{id}`     | Fetch one customer by numeric ID             |
| GET    | `/api/v1/customers/stats`    | Aggregate statistics over the dataset        |

### Query parameters for `GET /api/v1/customers`

| Parameter    | Type | Constraints              | Description                                |
|--------------|------|--------------------------|--------------------------------------------|
| `page`       | int  | ≥ 1, default 1           | 1-based page number                        |
| `page_size`  | int  | 1–100, default 20        | Items per page                             |
| `genre`      | str  | `Male`/`Female`, any case | Filter by genre                           |
| `min_age` / `max_age`       | int | 1–120        | Inclusive age range                        |
| `min_income` / `max_income` | int | ≥ 0          | Inclusive annual income range (k$)         |
| `min_score` / `max_score`   | int | 1–100        | Inclusive spending-score range             |
| `q`          | str  | 1–40 chars               | Search: substring of the zero-padded ID (e.g. `0042`) or genre prefix (e.g. `fem`) |
| `sort_by`    | enum | `customer_id`, `genre`, `age`, `annual_income_k`, `spending_score` | Sort field (default `customer_id`) |
| `sort_order` | enum | `asc` / `desc`           | Sort direction (default `asc`)             |

All filters, search and sorting compose freely.

### Examples

```bash
# Second page, 10 per page
curl "http://127.0.0.1:8000/api/v1/customers?page=2&page_size=10"

# High-income female customers (filters combine)
curl "http://127.0.0.1:8000/api/v1/customers?genre=female&min_income=120"

# Search by (zero-padded) customer id
curl "http://127.0.0.1:8000/api/v1/customers?q=0042"

# Top spenders first
curl "http://127.0.0.1:8000/api/v1/customers?sort_by=spending_score&sort_order=desc"

# One customer / aggregate stats
curl "http://127.0.0.1:8000/api/v1/customers/42"
curl "http://127.0.0.1:8000/api/v1/customers/stats"
```

Sample list response:

```json
{
  "items": [
    {"customer_id": 1, "genre": "Male", "age": 19, "annual_income_k": 15, "spending_score": 39}
  ],
  "pagination": {
    "page": 1, "page_size": 20, "total_items": 200,
    "total_pages": 10, "has_next": true, "has_prev": false
  }
}
```

## Validation & error handling

- Query/path parameters are validated by FastAPI (types, ranges, enums);
  violations return **422** with field-level details.
- Semantically inconsistent ranges (e.g. `min_age > max_age`) return **400**.
- Unknown customer IDs return **404**; database-level failures (e.g. import
  never run) return **500** with a hint to run the import script.
- Every non-2xx response uses one envelope:

```json
{"error": {"code": 404, "message": "Customer 999 not found"}}
```

- Search input is escaped so SQL `LIKE` wildcards (`%`, `_`) match literally,
  and all SQL uses bound parameters (no injection surface).

## Known limitations / future improvements

- **Read-only API** — no create/update/delete endpoints (and therefore no
  authentication story yet).
- **SQLite** is perfect for this dataset size but single-writer; a move to
  PostgreSQL (+ migrations) would be the path for concurrent production use.
- **No containerization or CI** — Docker and a GitHub Actions test workflow
  would make setup and regression-checking automatic.
- **Search is intentionally basic** (padded-ID substring + genre prefix);
  numeric-field search is already covered by range filters.
- **No rate limiting / observability** (structured logs, metrics).
- An **analytics endpoint** (e.g. income-vs-spending customer segmentation)
  would exploit this dataset's classic clustering structure.

These are tracked as GitHub issues on the repository.
