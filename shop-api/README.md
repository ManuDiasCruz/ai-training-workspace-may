# Shop API

A small production-style REST API built with **FastAPI** and **SQLite** on top of the
mall shopping customers dataset (`Shopping_data.csv`, 200 records sourced from Google
Drive). It exposes listing, pagination, filtering, search and aggregate statistics
over the customer data.

> Branch: `723-fh-shop-api`

## Dataset

Each record describes a mall customer:

| CSV column               | Type    | Notes                    |
| ------------------------ | ------- | ------------------------ |
| `CustomerID`             | string  | Zero-padded id (`0001`)  |
| `Genre`                  | string  | `Male` / `Female`        |
| `Age`                    | integer | 18–70                    |
| `Annual Income (k$)`     | integer | 15–137                   |
| `Spending Score (1-100)` | integer | Mall-assigned score      |

The raw CSV is committed at [`data/Shopping_data.csv`](data/Shopping_data.csv).

## Database design

A single SQLite table (the dataset is one flat entity, so one table is the honest
design — no artificial joins). The schema lives in [`app/database.py`](app/database.py):

```sql
CREATE TABLE customers (
    customer_id    INTEGER PRIMARY KEY,          -- "0001" -> 1
    genre          TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age            INTEGER NOT NULL CHECK (age > 0),
    annual_income  INTEGER NOT NULL CHECK (annual_income >= 0),   -- k$
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
```

Design decisions:

- **`customer_id` as `INTEGER PRIMARY KEY`** — the CSV ids are numeric with zero
  padding; storing them as integers gives free indexing and natural sorting, and the
  API re-pads on search so `0042` still finds customer 42.
- **`CHECK` constraints** mirror the dataset's documented ranges, so bad rows are
  rejected at the database layer, not just in application code.
- **Indexes** on `genre`, `age`, `annual_income` and `spending_score` support the
  API's filter combinations.
- The database file (`shop.db`) is generated locally and git-ignored; the CSV is the
  source of truth. The path can be overridden with the `SHOP_API_DB` env var (used by
  the test suite).

## Project layout

```
shop-api/
├── app/
│   ├── database.py      # SQLite connection helpers + schema
│   ├── main.py          # FastAPI app and endpoints
│   └── schemas.py       # Pydantic response models
├── data/
│   └── Shopping_data.csv
├── scripts/
│   └── import_data.py   # idempotent CSV -> SQLite import
├── tests/
│   └── test_api.py      # pytest + FastAPI TestClient suite
└── requirements.txt
```

## Setup

Requires **Python 3.10+**.

```bash
cd shop-api
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
# 1. Create the database and import the dataset (idempotent, safe to re-run)
python scripts/import_data.py

# 2. Start the API
uvicorn app.main:app --reload
```

The API is now at <http://127.0.0.1:8000>, with interactive OpenAPI docs at
<http://127.0.0.1:8000/docs>.

## API reference

| Method | Path                | Description                                    |
| ------ | ------------------- | ---------------------------------------------- |
| GET    | `/health`           | Liveness check + row count                     |
| GET    | `/customers`        | List customers (pagination, filters, sorting)  |
| GET    | `/customers/{id}`   | Fetch a single customer                        |
| GET    | `/customers/search` | Search by customer id or genre                 |
| GET    | `/stats`            | Aggregate statistics (overall and per genre)   |

### `GET /customers` query parameters

| Parameter               | Type / values                                            | Default       |
| ----------------------- | -------------------------------------------------------- | ------------- |
| `page`                  | int ≥ 1                                                   | `1`           |
| `page_size`             | int 1–100                                                 | `20`          |
| `genre`                 | `Male` \| `Female`                                        | —             |
| `min_age` / `max_age`   | int ≥ 0                                                   | —             |
| `min_income` / `max_income` | int ≥ 0 (annual income, k$)                           | —             |
| `min_score` / `max_score`   | int 1–100                                             | —             |
| `sort_by`               | `customer_id` \| `age` \| `annual_income` \| `spending_score` | `customer_id` |
| `order`                 | `asc` \| `desc`                                           | `asc`         |

### Examples

```bash
# Second page, 5 per page
curl "http://127.0.0.1:8000/customers?page=2&page_size=5"

# Female customers aged 30-40 with income >= 60k, highest spenders first
curl "http://127.0.0.1:8000/customers?genre=Female&min_age=30&max_age=40&min_income=60&sort_by=spending_score&order=desc"

# Single customer (404 with a JSON error if it does not exist)
curl "http://127.0.0.1:8000/customers/42"

# Search by (possibly zero-padded) id or genre
curl "http://127.0.0.1:8000/customers/search?q=0042"
curl "http://127.0.0.1:8000/customers/search?q=fem"

# Dataset statistics
curl "http://127.0.0.1:8000/stats"
```

Example `/customers` response:

```json
{
  "items": [
    {"customer_id": 42, "genre": "Male", "age": 24, "annual_income": 38, "spending_score": 92}
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

## Validation & error handling

- Query parameters are validated by FastAPI/Pydantic (types, ranges, enums) —
  invalid input returns **422** with a descriptive body.
- Inconsistent ranges (e.g. `min_age > max_age`) return **422**.
- Unknown customer ids return **404**; hitting the API before importing data
  returns **503** from `/health`.
- Filters are compiled to parameterised SQL — no string interpolation of user input.

## Tests

```bash
python -m pytest tests/ -v
```

The suite (13 tests) imports the CSV into a throwaway database
(`tests/test_shop.db`) and covers pagination, filtering, sorting, search,
error handling and the stats endpoint.

## Known limitations & future improvements

- **Read-only API** — no create/update/delete endpoints; the CSV is the only data
  source.
- **SQLite** — perfect for local use, but a real deployment would want
  PostgreSQL + migrations (e.g. Alembic).
- **No auth or rate limiting** — endpoints are open.
- **Search is basic** — substring match on id/genre only; a numeric-field search or
  full-text engine would be more useful.
- **No CI pipeline** — tests run locally; a GitHub Actions workflow would guard the
  branch.
- **No containerisation** — a Dockerfile would make setup one command.
