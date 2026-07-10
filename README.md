# Shopping Customers API

A small production-style REST API built on top of the
[Mall Customer Segmentation dataset](https://www.kaggle.com/datasets/vjchoudhary7/customer-segmentation-tutorial-in-python).
Records are imported from `data/Shopping_data.csv` into a local SQLite
database and exposed through a FastAPI service.

## Project description

The project demonstrates a small, fully runnable backend for an analytics
dataset:

- **Source data:** 200 mall customers with `CustomerID`, `Genre` (gender),
  `Age`, `Annual Income (k$)` and `Spending Score (1-100)`.
- **Storage:** SQLite, managed through SQLAlchemy 2.x ORM, with sensible
  `CHECK` constraints and indexes.
- **API:** FastAPI with Pydantic v2 schemas, pagination, filtering,
  search, sorting and basic write operations.
- **Tests:** pytest + `TestClient` running against an isolated SQLite
  file per test run.

## Database design

Single table `customers` (one row per customer).

| Column            | Type        | Notes                                            |
|-------------------|-------------|--------------------------------------------------|
| `id`              | INTEGER PK  | Auto-increment surrogate key.                    |
| `customer_code`   | VARCHAR(8)  | Unique, indexed — original `CustomerID` (`0001`).|
| `gender`          | VARCHAR(16) | `Male` or `Female` (source column `Genre`).      |
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

Requires Python 3.10+ (tested on 3.11).

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

## Endpoints summary

| Method | Path                  | Description                                |
|--------|-----------------------|--------------------------------------------|
| GET    | `/health`             | Liveness probe.                            |
| GET    | `/stats`              | Dataset aggregate statistics.              |
| GET    | `/customers`          | Paginated, filterable, searchable list.    |
| GET    | `/customers/{id}`     | Fetch a single customer by surrogate id.   |
| POST   | `/customers`          | Create a new customer.                     |
| DELETE | `/customers/{id}`     | Delete a customer.                         |

## Validation & error handling

- Request bodies and query parameters are validated by Pydantic; invalid
  input returns HTTP `422` with a structured detail payload.
- Inconsistent range filters (`min_age > max_age`, etc.) return HTTP
  `400`.
- Missing resources return HTTP `404` with `{"detail": "..."}`.
- Duplicate `customer_code` on create returns HTTP `409`.

## Known limitations & future improvements

- **Auth:** the API is fully open. A real deployment needs API keys or
  OAuth/JWT.
- **No update endpoint.** Only create / read / delete are exposed.
- **SQLite only.** Fine locally; for production swap in Postgres via
  `DATABASE_URL` and add Alembic migrations.
- **Search is intentionally simple** (`LIKE` over a couple of columns).
  Full-text search would need FTS5 or an external index.
- **No rate limiting / observability.** Logging, metrics and request
  tracing are out of scope for this exercise.
- **Tiny dataset.** All 200 rows fit in memory; the design choices would
  differ for millions of records (server-side cursor pagination,
  caching, etc.).

## Design

Stakeholder: Livia

The proposed first page is a customer-intelligence dashboard tailored to
this repository's mall-segmentation API. It turns the existing `/stats` and
`/customers` responses into an at-a-glance overview and a searchable customer
directory without implying capabilities the backend does not provide.

- **Penpot prototype:** [Shopping Customers — First-page Dashboard](https://design.penpot.app/#/view?file-id=bd542ff8-ca96-8077-8008-4e3234c73ebe&page-id=bd542ff8-ca96-8077-8008-4e3234c73ebf&section=interactions&frame-id=588bc1c3-3e59-801f-8008-4e3296f71ba5&index=0&share-id=86907e95-1cb8-8122-8008-4e32cd77d8a7)
- **Editable source reference:** [`design/shopping-customers-dashboard.svg`](design/shopping-customers-dashboard.svg)
- **Source branch:** `task002/shopping-api-dataset3`
- **Design delivery branch:** `cyan-h-livia-prototype-penpot`

### Page structure

1. A persistent navigation rail for Overview, Customers, Reports, and saved
   quick filters.
2. A search-first header that maps to `GET /customers?search=`.
3. A hero section with the primary task (`Explore customers`) and a secondary
   link to API documentation.
4. KPI cards backed by `GET /stats`: customer count, average spending score,
   average annual income, average age, and gender distribution.
5. A customer-directory preview backed by `GET /customers`, with filter,
   sort, pagination, create, and record-detail affordances.

### Developer handoff

| Token | Value | Use |
|---|---:|---|
| `--color-brand` | `#4F46E5` | Primary actions, active states, and links |
| `--color-accent` | `#A3E635` | High-emphasis CTA and live-data indicators |
| `--color-sidebar` | `#111827` | Persistent navigation surface |
| `--color-canvas` | `#F7F8FC` | Page background |
| `--color-text` | `#111827` | Primary text |
| `--color-muted` | `#64748B` | Supporting text and metadata |
| `--radius-card` | `18px` | KPI, chart, and table containers |
| `--space-page` | `32px` | Desktop content gutter |

- Target the supplied desktop frame first (`1440 × 1024`). At widths below
  `1024px`, collapse the left rail to icons; below `768px`, stack KPI cards and
  move customer rows to cards with the same field order.
- Keep a visible keyboard focus style (2px brand outline with 2px offset), use
  semantic headings/table markup, and expose spending score meaning in text as
  well as colour. Body text should remain at least 12px/16px depending on role.
- Load aggregate cards from `GET /stats`. Load the directory from
  `GET /customers?page=1&page_size=20`; debounce search by 300ms and preserve
  filters and sorting in the URL query string.
- Represent loading with card/table skeletons, show an inline retry state for
  API errors, and use a clear zero-state when a filter returns no customers.
- The first implementation milestone intentionally covers only this overview
  page. Reports, authentication, and update flows remain out of scope.
