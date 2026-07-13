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

**Stakeholder: Benny**

A Penpot design reference for the frontend of this API was created as part of Sprint task 4. Only the **first page** (Customers Dashboard) is designed; further pages (customer detail, add-customer form, statistics) will follow in later iterations.

### Prototype

- **Penpot file:** [Shopping Customers — Frontend Prototype (Task 4 · Stakeholder: Benny)](https://design.penpot.app/#/workspace?team-id=8580c946-af19-8023-8008-18c60abb3381&project-id=8580c946-af19-8023-8008-18c60abb5635&file-id=86907e95-1cb8-8122-8008-4fc64a69a769&page-id=86907e95-1cb8-8122-8008-4fc64a69a76a)
- **Page:** `01 · Dashboard (first page)` · **Board:** `01 · Customers Dashboard — Desktop 1440` (1440×1024)
- Access: the file lives in the *Your Penpot* team Drafts of the design account; ask the design team for an invite if the link does not open.
- Implementation ticket: [issue #290](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/290)
- Related branches: source `task002/shopping-api-dataset3` · design docs `fable-eh-benny-prototype-penpot`

### What the first page contains

| Region | Contents | API mapping |
|---|---|---|
| Sidebar (248 px) | Logo, nav (Dashboard, Customers, Statistics, Add customer, Settings), health card | `GET /health` |
| Top bar | Title + breadcrumb, global search, "+ Add customer" | `?search=`, `POST /customers` |
| Stat cards | Total customers (gender split), avg. age, avg. income, avg. spending score | `GET /stats` |
| Filter bar | Gender, age/income/score ranges, sort + order | `GET /customers` query params |
| Table | Code, gender badge, age, income (k$), score progress bar, View/Delete | `GET /customers`, `DELETE /customers/{id}` |
| Footer | "Showing 1–8 of 200", pagination | `page`, `page_size` |

### Design tokens (for the frontend team)

- Primary `#4F46E5` · sidebar/dark text `#101828` · muted text `#667085`
- Page background `#F6F8FB` · cards `#FFFFFF` with border `#EAECF0`
- Status colors: success `#12B76A` · warning `#F79009` · danger `#F04438`
- Gender badges: Male `#EFF8FF`/`#175CD3` · Female `#FDF2FA`/`#C11574`
- Spending-score bar thresholds: <40 danger · 40–69 warning · ≥70 success
- Typography: Source Sans Pro (400/600/700) · radii: cards 12 px, controls 8 px

### Notes for developers

- Filter controls map 1:1 to the API query params: `gender`, `min_age`, `max_age`, `min_income`, `max_income`, `min_score`, `max_score`, `sort_by`, `order`.
- Handle 400/404/409/422 responses with inline errors or toasts (see "Validation & error handling" above).
- The API exposes no update endpoint — the UI deliberately has no edit action.
- Mock data in the design uses the first 8 real rows of `data/Shopping_data.csv` and the real dataset aggregates (200 customers, 112 F / 88 M, avg age 38.9, avg income $60.6k, avg score 50.2).
