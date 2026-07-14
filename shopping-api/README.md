# 🛍️ Shopping API

A small, production-style backend that turns the **mall-customers shopping
dataset** into a queryable REST API. Built with **FastAPI**, **SQLAlchemy** and
**SQLite** — it imports the CSV into a local database and exposes endpoints for
listing, pagination, filtering, search and aggregate statistics.

> Branch: `ops-ehi-shopping-api-dataset` · Project directory: [`shopping-api/`](.)

---

## Project description

The source data (`data/Shopping_data.csv`, 200 rows) describes shopping-mall
customers with the following columns:

| CSV column               | Meaning                          | Example |
|--------------------------|----------------------------------|---------|
| `CustomerID`             | Zero-padded 4-digit id           | `0001`  |
| `Genre`                  | Gender (`Male` / `Female`)       | `Male`  |
| `Age`                    | Age in years                     | `19`    |
| `Annual Income (k$)`     | Annual income in thousands USD   | `15`    |
| `Spending Score (1-100)` | Mall-assigned spending score     | `39`    |

The service:

1. Reads and validates the CSV.
2. Persists it into a local SQLite database.
3. Serves the data through a documented REST API (interactive docs at `/docs`).

---

## Database design

A single table is sufficient for this flat dataset — each row is one
independent customer, with no relationships to model.

**Table `customers`**

| Column            | Type    | Notes                                                        |
|-------------------|---------|--------------------------------------------------------------|
| `customer_id`     | TEXT PK | Kept as text to preserve the `0001` zero-padding & stability |
| `gender`          | TEXT    | Renamed from CSV `Genre`; `CHECK` in (`Male`,`Female`)       |
| `age`             | INTEGER | `CHECK` 0–120                                                |
| `annual_income_k` | INTEGER | Annual income in k$; `CHECK` ≥ 0                             |
| `spending_score`  | INTEGER | `CHECK` 1–100                                                |

**Indexes** — `gender`, `age`, `annual_income_k`, `spending_score` are indexed
individually (they are the filter/sort fields), plus a composite index on
`(annual_income_k, spending_score)` for the common income+score query.

**Design choices**

- **SQLite** — zero-config, file-based, ideal for a small read-mostly dataset
  and fully runnable locally.
- **`CHECK` constraints** enforce data integrity at the storage layer,
  independent of the API validation layer.
- **Idempotent import** — the loader replaces the table by default, so
  re-running always reproduces exactly the CSV contents.

The schema lives in [`app/models.py`](app/models.py); the importer with row-level
validation is in [`app/importer.py`](app/importer.py).

---

## Setup instructions

Requires **Python 3.10+**.

```bash
cd shopping-api

# 1. Create & activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# .venv\Scripts\activate           # Windows (PowerShell/CMD)
# source .venv/bin/activate        # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt
```

---

## Execution steps

```bash
# 1. Build the local database from the CSV
python -m scripts.import_data
#   -> Imported 200 customers into .../shopping.db

# 2. Run the API
uvicorn app.main:app --reload
#   -> http://127.0.0.1:8000  (interactive docs at /docs)
```

> On first startup the API also **auto-seeds** an empty database from the CSV,
> so step 1 is optional for a quick start. Set `SHOPPING_AUTO_SEED=0` to disable.

**Run the tests**

```bash
pytest            # 17 tests: listing, pagination, filtering, search, validation
```

**Configuration (environment variables)**

| Variable             | Default              | Purpose                              |
|----------------------|----------------------|--------------------------------------|
| `SHOPPING_DB_PATH`   | `./shopping.db`      | SQLite file location                 |
| `SHOPPING_CSV_PATH`  | `./data/Shopping_data.csv` | Source CSV for the importer    |
| `SHOPPING_AUTO_SEED` | `1`                  | Auto-seed empty DB on startup (`0`=off) |

---

## API usage examples

Base URL: `http://127.0.0.1:8000`

| Method | Path                       | Description                                   |
|--------|----------------------------|-----------------------------------------------|
| GET    | `/`                        | API index                                     |
| GET    | `/health`                  | Health check + record count                   |
| GET    | `/customers`               | List with pagination, filtering, search, sort |
| GET    | `/customers/{customer_id}` | Fetch a single customer                       |
| GET    | `/stats`                   | Aggregate statistics                          |

### List query parameters

| Param                                     | Type    | Rules                    | Description                         |
|-------------------------------------------|---------|--------------------------|-------------------------------------|
| `page`                                    | int     | ≥ 1 (default 1)          | Page number                         |
| `page_size`                               | int     | 1–100 (default 20)       | Records per page                    |
| `gender`                                  | enum    | `Male` / `Female`        | Filter by gender                    |
| `min_age` / `max_age`                     | int     | 0–120                    | Age range                           |
| `min_income` / `max_income`               | int     | ≥ 0                      | Annual income (k$) range            |
| `min_spending_score` / `max_spending_score` | int   | 1–100                    | Spending-score range                |
| `search`                                  | string  | 1–50 chars               | Substring match on id or gender     |
| `sort_by`                                 | enum    | `customer_id`/`age`/`annual_income_k`/`spending_score` | Sort field |
| `order`                                   | enum    | `asc` / `desc`           | Sort direction                      |

### Examples

```bash
# Paginated listing
curl "http://127.0.0.1:8000/customers?page=1&page_size=2"

# Filter: females aged 30-35, highest age first
curl "http://127.0.0.1:8000/customers?gender=Female&min_age=30&max_age=35&sort_by=age&order=desc"

# Filter: middle-income big spenders
curl "http://127.0.0.1:8000/customers?min_income=50&max_income=80&min_spending_score=60"

# Search by id
curl "http://127.0.0.1:8000/customers?search=0007"

# Single record
curl "http://127.0.0.1:8000/customers/0042"

# Aggregate stats
curl "http://127.0.0.1:8000/stats"
```

**Sample list response**

```json
{
  "meta": { "page": 1, "page_size": 2, "total": 200, "total_pages": 100 },
  "items": [
    { "customer_id": "0001", "gender": "Male", "age": 19, "annual_income_k": 15, "spending_score": 39 },
    { "customer_id": "0002", "gender": "Male", "age": 21, "annual_income_k": 15, "spending_score": 81 }
  ]
}
```

**Sample stats response**

```json
{
  "total_customers": 200,
  "by_gender": [{ "gender": "Female", "count": 112 }, { "gender": "Male", "count": 88 }],
  "age": { "min": 18.0, "max": 70.0, "avg": 38.85 },
  "annual_income_k": { "min": 15.0, "max": 137.0, "avg": 60.56 },
  "spending_score": { "min": 1.0, "max": 99.0, "avg": 50.2 }
}
```

### Validation & error handling

- **422 Unprocessable Entity** — a parameter violates its own constraints
  (e.g. `page_size=999`, `page=0`, `gender=Other`). Handled automatically by
  FastAPI/Pydantic.
- **400 Bad Request** — a cross-field rule is violated, e.g. `min_age > max_age`
  → `{"detail": "min_age (60) cannot be greater than max_age (20)"}`.
- **404 Not Found** — unknown `customer_id`
  → `{"detail": "Customer '9999' not found"}`.
- **500 Internal Server Error** — unexpected errors return a uniform
  `{"detail": "Internal server error"}` body instead of a stack trace.

---

## Project structure

```text
shopping-api/
├── app/
│   ├── config.py       # env-driven paths & DB URL
│   ├── database.py     # SQLAlchemy engine, session, get_db dependency
│   ├── models.py       # Customer ORM model + constraints/indexes
│   ├── schemas.py      # Pydantic request/response models
│   ├── crud.py         # filtering / search / pagination / stats queries
│   ├── importer.py     # CSV -> SQLite loader with row validation
│   └── main.py         # FastAPI app, endpoints, error handlers
├── scripts/
│   └── import_data.py  # CLI wrapper around the importer
├── tests/
│   ├── conftest.py     # isolated temp-DB fixture
│   └── test_api.py     # 17 automated API tests
├── data/
│   └── Shopping_data.csv
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Known limitations & future improvements

- **Read-only API** — no create/update/delete endpoints yet.
- **Search is limited** — the dataset has no free-text field, so `search` only
  matches `customer_id`/`gender` substrings (note: `search=male` also matches
  `Female`). A dataset with names/products would warrant full-text search.
- **SQLite / single node** — fine for this dataset, but not for high write
  concurrency or horizontal scaling.
- **No authentication / rate limiting** — every endpoint is public.
- **Offset pagination** — simple, but cursor/keyset pagination scales better on
  large tables.
- **No CI pipeline** — tests run locally only.

See the repository **Issues** (tagged with this branch) for concrete next steps.
