# Shopping API

A small production-style REST API over the **Mall Customers** shopping dataset
(200 customer records sourced from Google Drive). The dataset is persisted in a
local SQLite database and exposed through a FastAPI service with pagination,
filtering, search, and aggregate statistics.

Built on branch `731-fa-eh-shopapi`.

## Project structure

```
shopapi/
├── app/
│   ├── database.py      # SQLite connection helpers + schema DDL
│   ├── main.py          # FastAPI app and endpoints
│   └── schemas.py       # Pydantic response models and enums
├── data/
│   ├── Shopping_data.csv  # Source dataset (committed)
│   └── shopping.db        # Generated SQLite database (gitignored)
├── scripts/
│   └── import_data.py   # Idempotent CSV → SQLite import
├── tests/
│   ├── conftest.py      # TestClient + throwaway DB fixture
│   └── test_api.py      # Automated API tests
├── requirements.txt
└── README.md
```

## Dataset

`data/Shopping_data.csv` — 200 rows, one per mall customer:

| CSV column              | Type    | Notes                    |
|-------------------------|---------|--------------------------|
| CustomerID              | int     | Unique, zero-padded 1–200 |
| Genre                   | text    | `Male` / `Female`        |
| Age                     | int     | 18–70 in this dataset    |
| Annual Income (k$)      | int     | 15–137                   |
| Spending Score (1-100)  | int     | 1–99                     |

## Database design

Single-table SQLite schema (the dataset is one flat entity, so no joins are
needed). Column names are normalized to `snake_case` and constraints mirror the
dataset's documented domains:

```sql
CREATE TABLE customers (
    id              INTEGER PRIMARY KEY,                                  -- CustomerID
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),        -- Annual Income (k$)
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
```

Indexes on `genre`, `age`, `annual_income_k`, and `spending_score` support the
API's filter and sort paths. The import script validates every CSV row (types,
genre values, value ranges) before inserting, and is idempotent — re-running it
replaces the table contents.

## Setup

Requires Python 3.10+.

```bash
cd shopapi
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
# 1. Build the database from the CSV (creates data/shopping.db)
python scripts/import_data.py

# 2. Start the API
uvicorn app.main:app --reload
```

The API serves at `http://127.0.0.1:8000`. Interactive docs (Swagger UI) are at
`http://127.0.0.1:8000/docs`.

## Running the tests

```bash
python -m pytest tests -v
```

The suite builds a temporary SQLite database from the real CSV (via the same
import code path) so persistence, querying, and the HTTP layer are all covered.

## API reference

| Method | Path                     | Description |
|--------|--------------------------|-------------|
| GET    | `/health`                | Liveness check |
| GET    | `/customers`             | List customers with pagination, filtering, sorting |
| GET    | `/customers/{id}`        | Fetch one customer (404 if absent) |
| GET    | `/customers/search`      | Search by customer code or genre |
| GET    | `/stats`                 | Overall and per-genre aggregates |

### `GET /customers` query parameters

| Parameter    | Type | Default | Constraints |
|--------------|------|---------|-------------|
| `page`       | int  | 1       | ≥ 1 |
| `page_size`  | int  | 20      | 1–100 |
| `genre`      | enum | —       | `Male` or `Female` |
| `min_age` / `max_age`       | int | — | 1–120 |
| `min_income` / `max_income` | int | — | ≥ 0 (k$) |
| `min_score` / `max_score`   | int | — | 1–100 |
| `sort_by`    | enum | `id`    | `id`, `age`, `annual_income_k`, `spending_score` |
| `order`      | enum | `asc`   | `asc`, `desc` |

Inverted ranges (e.g. `min_age=60&max_age=20`), unknown enum values, and
out-of-range values are rejected with `422`.

### Examples

```bash
# Second page, 10 per page
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"

# High-income women with low spending scores, highest income first
curl "http://127.0.0.1:8000/customers?genre=Female&min_income=100&max_score=30&sort_by=annual_income_k&order=desc"

# One customer
curl "http://127.0.0.1:8000/customers/42"

# Search by zero-padded customer code or genre substring
curl "http://127.0.0.1:8000/customers/search?q=0042"
curl "http://127.0.0.1:8000/customers/search?q=male"

# Aggregates
curl "http://127.0.0.1:8000/stats"
```

Sample list response:

```json
{
  "items": [
    {"id": 1, "genre": "Male", "age": 19, "annual_income_k": 15, "spending_score": 39}
  ],
  "total": 200,
  "page": 1,
  "page_size": 20,
  "pages": 10
}
```

## Error handling

- `404` — customer id not found, or `/stats` on an empty database.
- `422` — invalid query parameters (bad enums, out-of-range values, inverted
  min/max pairs, empty search term), with a descriptive message.
- `503` — database file missing (import script not yet run).

## Known limitations & future improvements

- **Read-only API** — no POST/PUT/DELETE endpoints; the dataset is only
  refreshed through the import script.
- **Naive search** — substring match over customer code and genre; a
  full-text/multi-field search would be more useful on a richer dataset.
- **No auth or rate limiting** — the API is intended for local use only.
- **SQLite** — perfect for a 200-row local dataset, but a client/server RDBMS
  (PostgreSQL) plus a migration tool (Alembic) would be the next step for a
  real deployment.
- **No CI pipeline** — tests run locally; a GitHub Actions workflow would keep
  the branch green automatically.
- **Dataset naming** — the source CSV calls the gender column `Genre`; the API
  keeps that name for fidelity with the dataset, at the cost of a slightly
  confusing field name.
