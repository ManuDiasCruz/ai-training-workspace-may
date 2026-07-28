# Shop API

A small production-style REST API over the mall-customers shopping dataset
(`Shopping_data.csv`, 200 records). The dataset is persisted into a local
SQLite database and exposed through a FastAPI service with listing,
pagination, filtering, search, sorting and aggregate statistics.

**Branch:** `723-feh-shop-api`

## Dataset

Source: `data/Shopping_data.csv` (downloaded from Google Drive).

| CSV column               | Type    | Notes                       |
| ------------------------ | ------- | --------------------------- |
| `CustomerID`             | integer | unique, zero-padded in CSV  |
| `Genre`                  | text    | `Male` / `Female`           |
| `Age`                    | integer | 18–70 in this dataset       |
| `Annual Income (k$)`     | integer | thousands of dollars        |
| `Spending Score (1-100)` | integer | mall-assigned score, 1–100  |

## Database design

The dataset is a single flat entity, so the schema is one indexed table in
SQLite (`data/shop.db`, created by the import script):

```sql
CREATE TABLE customers (
    id              INTEGER PRIMARY KEY,                                  -- CustomerID
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
-- single-column indexes on genre, age, annual_income_k, spending_score
```

Design choices:

- **SQLite** — zero-setup, file-based, ideal for a local, read-mostly dataset
  of this size; the connection layer (`app/database.py`) is isolated so a
  different engine could be swapped in later.
- **CHECK constraints** mirror the import-time validation so invalid data
  cannot enter the table through any path.
- **Indexes** on every filterable column keep the filter/sort queries fast.
- The database path can be overridden with the `SHOP_API_DB` environment
  variable (used by the test suite to run against a throwaway database).

## Project layout

```
shop-api/
├── app/
│   ├── database.py      # SQLite helpers + schema
│   ├── models.py        # Pydantic response models
│   └── main.py          # FastAPI app and endpoints
├── scripts/
│   └── import_data.py   # CSV → SQLite import (idempotent)
├── tests/
│   ├── conftest.py      # test client over a temp database
│   └── test_api.py      # 14 API tests
├── data/
│   └── Shopping_data.csv
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.10+ (developed on 3.12).

```bash
cd shop-api
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Running

```bash
# 1. Import the dataset into SQLite (creates data/shop.db, safe to re-run)
python scripts/import_data.py

# 2. Start the API
uvicorn app.main:app --reload --port 8000
```

Interactive docs (Swagger UI): <http://127.0.0.1:8000/docs>

## Running the tests

```bash
python -m pytest tests -v
```

The suite spins up a `TestClient` against a temporary database built from the
real CSV, and covers listing, pagination, filtering, search, sorting, stats,
and the error paths (400/404/422).

> If your environment restricts the system temp directory, pass a local one:
> `python -m pytest tests -v --basetemp=.pytest_tmp`

## API reference

| Method | Path              | Description                                        |
| ------ | ----------------- | -------------------------------------------------- |
| GET    | `/health`         | Liveness check                                     |
| GET    | `/customers`      | List customers (pagination, filters, search, sort) |
| GET    | `/customers/{id}` | Fetch one customer by id (404 if missing)          |
| GET    | `/customers/stats`| Aggregate stats, overall and per genre             |

### `GET /customers` query parameters

| Parameter    | Type / range                                      | Default | Description                       |
| ------------ | ------------------------------------------------- | ------- | --------------------------------- |
| `page`       | int ≥ 1                                            | 1       | 1-based page number               |
| `page_size`  | int 1–100                                          | 20      | items per page                    |
| `genre`      | `Male` / `Female` (case-insensitive)               | –       | filter by genre                   |
| `min_age` / `max_age`       | int 1–120                           | –       | inclusive age range               |
| `min_income` / `max_income` | int ≥ 0                             | –       | inclusive annual income (k$)      |
| `min_score` / `max_score`   | int 1–100                           | –       | inclusive spending score range    |
| `q`          | string                                             | –       | numeric → exact id match; text → genre substring |
| `sort_by`    | `id`, `genre`, `age`, `annual_income_k`, `spending_score` | `id` | sort column               |
| `sort_dir`   | `asc` / `desc`                                     | `asc`   | sort direction                    |

### Examples

```bash
# Second page, 10 per page
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"

# Female customers earning 100k$+ sorted by income (descending)
curl "http://127.0.0.1:8000/customers?genre=female&min_income=100&sort_by=annual_income_k&sort_dir=desc"

# High spenders aged 40 or younger
curl "http://127.0.0.1:8000/customers?max_age=40&min_score=80"

# Search: numeric term matches an id
curl "http://127.0.0.1:8000/customers?q=42"

# Single customer / aggregate stats
curl "http://127.0.0.1:8000/customers/7"
curl "http://127.0.0.1:8000/customers/stats"
```

Sample list response:

```json
{
  "items": [
    {"id": 197, "genre": "Female", "age": 45, "annual_income_k": 126, "spending_score": 28}
  ],
  "page": 1,
  "page_size": 3,
  "total_items": 9,
  "total_pages": 3
}
```

## Validation and error handling

- Query/path parameters are validated by FastAPI/Pydantic → `422` with field
  details for out-of-range or malformed values.
- Inverted ranges (e.g. `min_age > max_age`) → `400` with a clear message.
- Unknown customer id → `404`.
- API called before the import script has run → `503` with a hint.
- The import script validates every CSV row (header, types, ranges) and is
  idempotent (upsert by customer id).

## Known limitations / future improvements

- **Read-only API** — no create/update/delete endpoints; the dataset only
  changes via the import script.
- **Search is minimal** — numeric-id or genre substring only; a richer search
  (multi-field, fuzzy) would need FTS or a search engine.
- **No auth or rate limiting** — fine locally, required before any real
  deployment.
- **SQLite** — perfect for this scale, but a client/server database
  (PostgreSQL) plus migrations (Alembic) would suit multi-writer production
  use.
- **No CI pipeline** — tests run locally; a GitHub Actions workflow would run
  them on every push.
- **No containerization** — a Dockerfile would make the runtime reproducible.
