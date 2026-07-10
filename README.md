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

## Design

**Stakeholder: Jessy**

- **Penpot prototype (first page only):** [Shopping Customers · First-page intelligence · Jessy](https://design.penpot.app/#/view?file-id=86907e95-1cb8-8122-8008-4e2c4d0e20c4&page-id=86907e95-1cb8-8122-8008-4e2c4d0e20c5&section=interactions&index=0)
- **Reference screen:** `Customer intelligence`, desktop `1440 × 1024`.
- **Source branch:** `task002/shopping-api-dataset3`.
- **Design handoff branch:** `purple-eh-jessy-prototype-penpot`.

The first page is a customer-intelligence dashboard rather than a product
catalogue. It mirrors the repository's mall-customer dataset and exposes the
existing API capabilities through a focused overview: aggregate KPIs,
customer-code/gender search, pagination, filter shortcuts, gender mix and a
create-customer entry point. The prototype uses real sample values from
`Shopping_data.csv` and names the major canvas layers for easier inspection.

### Frontend implementation map

| UI area | API/data contract | Implementation notes |
|---|---|---|
| KPI cards and gender mix | `GET /stats` | Bind `total_customers`, `by_gender`, `avg_age`, `avg_annual_income_k`, and `avg_spending_score`. Do not hard-code the prototype's snapshot values. |
| Customer explorer | `GET /customers?page=1&page_size=20` | Render `customer_code`, `gender`, `age`, `annual_income_k`, and `spending_score`. Preserve the server's `total`, `page`, and `page_size` response values for pagination. |
| Search field | `search` | Debounce client input and send non-empty values only. The API matches `customer_code` and `gender` case-insensitively. |
| Gender selector | `gender=Male|Female` | The unselected state omits the parameter; the two selected values must use the API's exact casing. |
| Filter shortcuts | `min_age`, `max_age`, `min_income`, `min_score`, `sort_by`, `order` | Young high spenders: `min_age=18&max_age=25&min_score=70`. High income: `min_income=100`. Top spending score: `sort_by=spending_score&order=desc`. |
| Add customer | `POST /customers` | Open a form for the five fields in `CustomerCreate`; show inline 422 errors and a clear duplicate-code message for HTTP 409. |

### Visual and interaction notes

- Core palette: ink `#0B1220`, panel `#FFFFFF`, canvas `#F6F8FB`, coral
  action `#FF6B4A`, mint success `#2FD0A6`, and border `#E4E7EC`.
- Use an 8 px spacing grid, 12 px control radii, 18–22 px card radii and a
  readable sans-serif such as Inter. Keep the dark navigation at 236 px on
  desktop and maintain a minimum 16 px inner gutter at narrow widths.
- Provide loading skeletons for stats and rows, an inline retry state for API
  failures, an empty-results state that retains active filters, and disabled
  previous/next controls at the pagination boundaries.
- All interactive controls need visible keyboard focus, programmatic labels,
  and text/icon contrast that meets WCAG AA. Do not rely on score colour alone;
  retain the numeric value shown in the table.

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
