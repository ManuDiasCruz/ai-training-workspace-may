# Shopping Customers API

A small production-style REST API built on top of the provided
[shopping dataset in Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing),
a copy of the Mall Customer Segmentation dataset. Records are imported from
`data/Shopping_data.csv` into a local SQLite database and exposed through a
FastAPI service.

## Project description

The project demonstrates a small, fully runnable backend for an analytics
dataset:

- **Source data:** 200 mall customers with `CustomerID`, `Genre` (gender),
  `Age`, `Annual Income (k$)` and `Spending Score (1-100)`.
- **Storage:** SQLite, managed through SQLAlchemy 2.x ORM, with sensible
  `CHECK` constraints and indexes.
- **API:** FastAPI with Pydantic v2 schemas, pagination, filtering,
  search, sorting and basic write operations.
- **Tests:** pytest + `httpx.ASGITransport` running against an isolated SQLite
  file per test run, with requests sent directly to the ASGI application.

### Dataset inspection

The supplied CSV has one header row and 200 unique customer rows. There are no
empty values in the source fields. The observed values are:

| Source field | Imported field | Observed values / range |
|---|---|---|
| `CustomerID` | `customer_code` | `0001`–`0200`, unique |
| `Genre` | `gender` | `Male`, `Female` |
| `Age` | `age` | 18–70 |
| `Annual Income (k$)` | `annual_income_k` | 15–137 |
| `Spending Score (1-100)` | `spending_score` | 1–99 |

`CustomerID` is loaded as text so leading zeros are preserved. The importer
requires all five columns, validates each row, and rolls the transaction back
instead of persisting a partially malformed source file.

## Database design

Single table `customers` (one row per customer).

| Column            | Type        | Notes                                            |
|-------------------|-------------|--------------------------------------------------|
| `id`              | INTEGER PK  | Auto-increment surrogate key.                    |
| `customer_code`   | VARCHAR(8)  | Unique, indexed — original `CustomerID` (`0001`).|
| `gender`          | VARCHAR(16) | `Male` or `Female`; enforced by `CHECK`.         |
| `age`             | INTEGER     | `CHECK age BETWEEN 0 AND 130`.                   |
| `annual_income_k` | INTEGER     | Annual income in thousands of dollars (`>= 0`).  |
| `spending_score`  | INTEGER     | `CHECK spending_score BETWEEN 1 AND 100`.        |

Additional indexes: `ix_customers_customer_code` (unique) and a composite
`ix_customers_gender_age` to speed up the most common filter combination.

### Why a single table?

The dataset is a flat survey/segmentation snapshot — there are no
relationships, transactions or time series. A single normalized table
captures the data faithfully without over-engineering. The schema is
written so a future order/transaction table could reference
`customers.id` as a foreign key.

## Project layout

```
.
├── app/
│   ├── __init__.py
│   ├── crud.py          # Query helpers
│   ├── database.py      # SQLAlchemy engine / session
│   ├── main.py          # FastAPI app and routes
│   ├── models.py        # ORM models
│   └── schemas.py       # Pydantic request / response models
├── data/
│   └── Shopping_data.csv
├── scripts/
│   └── import_data.py   # CSV → SQLite importer
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.10+ (tested on 3.10).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execution

Import the dataset into a local SQLite database (`shopping.db` in the
repo root, created on first run):

```bash
python -m scripts.import_data
```

The import is idempotent: rows already present under the same
`customer_code` are skipped. A successful first import reports 200 inserted
customers; another run reports zero.

Run the API:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Then visit:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc:      <http://127.0.0.1:8000/redoc>
- Health:     <http://127.0.0.1:8000/health>

Run the test suite:

```bash
python -m pytest -q
```

The `DATABASE_URL` environment variable overrides the SQLite location,
e.g. `DATABASE_URL=sqlite:////tmp/shopping.db`.

## API usage examples

### List customers with pagination

```bash
curl "http://127.0.0.1:8000/customers?page=1&page_size=5"
```

The response includes `total`, `page`, `page_size`, `total_pages`, `has_next`,
`has_previous`, and the current page's `items`.

### Filter

```bash
# Female customers aged 18–25, top spending scores first
curl "http://127.0.0.1:8000/customers?gender=Female&min_age=18&max_age=25&sort_by=spending_score&order=desc&page_size=5"

# High-income customers
curl "http://127.0.0.1:8000/customers?min_income=100"
```

Supported filters: `gender`, `min_age`, `max_age`, `min_income`,
`max_income`, `min_score`, `max_score`.
Sortable columns: `id`, `age`, `annual_income_k`, `spending_score`,
`customer_code`. Order: `asc` (default) or `desc`.

### Search

`search` does a case-insensitive substring match on `customer_code` and
`gender`:

```bash
curl "http://127.0.0.1:8000/customers?search=0042"
```

### Single customer

```bash
curl "http://127.0.0.1:8000/customers/1"
```

### Dataset statistics

```bash
curl "http://127.0.0.1:8000/stats"
```

Returns total count, gender breakdown and averages.

### Create / delete

```bash
curl -X POST "http://127.0.0.1:8000/customers" \
     -H "Content-Type: application/json" \
     -d '{"customer_code":"9999","gender":"Female","age":28,"annual_income_k":60,"spending_score":55}'

curl -X DELETE "http://127.0.0.1:8000/customers/201"
```

### Update

```bash
curl -X PATCH "http://127.0.0.1:8000/customers/42" \
     -H "Content-Type: application/json" \
     -d '{"annual_income_k":45,"spending_score":95}'
```

## Endpoints summary

| Method | Path                  | Description                                |
|--------|-----------------------|--------------------------------------------|
| GET    | `/health`             | Liveness probe.                            |
| GET    | `/stats`              | Dataset aggregate statistics.              |
| GET    | `/customers`          | Paginated, filterable, searchable list.    |
| GET    | `/customers/{id}`     | Fetch a single customer by surrogate id.   |
| POST   | `/customers`          | Create a new customer.                     |
| PATCH  | `/customers/{id}`     | Update selected fields on a customer.      |
| DELETE | `/customers/{id}`     | Delete a customer.                         |

## Validation & error handling

- Request bodies and query parameters are validated by Pydantic; invalid
  input returns HTTP `422` with a structured detail payload.
- Inconsistent range filters (`min_age > max_age`, etc.) return HTTP
  `400`.
- Missing resources return HTTP `404` with `{"detail": "..."}`.
- Duplicate `customer_code` on create/update returns HTTP `409`.
- An empty update request returns HTTP `400`.
- CSV imports fail atomically when columns are missing or values are outside
  the model's allowed domains.

## Known limitations & future improvements

- **Auth:** the API is fully open. A real deployment needs API keys or
  OAuth/JWT.
- **SQLite only.** Fine locally; for production swap in Postgres via
  `DATABASE_URL` and add Alembic migrations.
- **Search is intentionally simple** (`LIKE` over a couple of columns).
  Full-text search would need FTS5 or an external index.
- **No rate limiting / observability.** Logging, metrics and request
  tracing are out of scope for this exercise.
- **No write audit trail or bulk import API.** Future versions could record
  source/import metadata and expose authenticated, background import jobs.
- **Tiny dataset.** All 200 rows fit in memory; the design choices would
  differ for millions of records (server-side cursor pagination,
  caching, etc.).
