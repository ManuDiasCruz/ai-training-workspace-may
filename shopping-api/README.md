# Shopping Customers API

A small production-style REST API built with **FastAPI** and **SQLite** on top of the
mall shopping dataset (`Shopping_data.csv`, 200 customers). The raw CSV is versioned in
[`data/Shopping_data.csv`](data/Shopping_data.csv), imported into a local SQLite database
by a validated import pipeline, and exposed through paginated, filterable REST endpoints.

## Dataset

Source: `Shopping_data.csv` (Google Drive). 200 rows, one per customer:

| CSV column               | Type    | Notes                          |
| ------------------------ | ------- | ------------------------------ |
| `CustomerID`             | integer | unique, `0001`–`0200`          |
| `Genre`                  | text    | `Male` or `Female`             |
| `Age`                    | integer | 18–70 in this dataset          |
| `Annual Income (k$)`     | integer | thousands of dollars, 15–137   |
| `Spending Score (1-100)` | integer | store-assigned score, 1–99     |

## Database design

Single-table SQLite schema (`app/database.py`), with CSV columns normalised to
snake_case. SQLite was chosen because the dataset is small, read-only and local —
no server process to manage, and the DB is rebuilt from the CSV at any time.

```sql
CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
```

Indexes on `genre`, `age`, `annual_income_k` and `spending_score` support the
filterable fields. `CHECK` constraints enforce data quality at the storage layer,
and the importer (`app/import_data.py`) validates every row (header shape, types,
value ranges) before anything is written. The import runs in a single transaction
and replaces the table contents, so it is idempotent and never half-applied.

The generated `data/shopping.db` is intentionally **not** committed — it is a
build artifact reproducible from the CSV.

## Project structure

```text
shopping-api/
├── app/
│   ├── database.py      # DB path resolution, connection factory, schema DDL
│   ├── import_data.py   # validated CSV → SQLite import pipeline (CLI)
│   ├── main.py          # FastAPI app: endpoints, filtering, error handling
│   └── schemas.py       # Pydantic response models
├── data/
│   └── Shopping_data.csv
├── tests/
│   └── test_api.py      # end-to-end API tests (pytest + TestClient)
├── conftest.py
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.10+ (developed on 3.12). From the `shopping-api` directory:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Running

```bash
# 1. Build the database from the CSV (idempotent, safe to re-run)
python -m app.import_data

# 2. Start the API
uvicorn app.main:app --reload
```

The API is now on <http://127.0.0.1:8000> with interactive OpenAPI docs at
<http://127.0.0.1:8000/docs>. The database location can be overridden with the
`SHOPPING_DB_PATH` environment variable (used by the test suite).

## Endpoints

| Method | Path              | Description                                        |
| ------ | ----------------- | -------------------------------------------------- |
| GET    | `/health`         | liveness check + row count                         |
| GET    | `/customers`      | list customers: pagination, filters, sorting       |
| GET    | `/customers/search` | basic search across genre and numeric fields     |
| GET    | `/customers/{id}` | fetch one customer (404 if absent)                 |
| GET    | `/stats`          | dataset summary + per-genre breakdown              |

### Query parameters for `/customers`

- `page` (default 1), `page_size` (default 20, max 100)
- `genre` — `Male`/`Female`, case-insensitive
- `min_age` / `max_age`, `min_income` / `max_income`, `min_score` / `max_score`
- `sort_by` — `customer_id` | `genre` | `age` | `annual_income_k` | `spending_score`
- `order` — `asc` | `desc`

### Examples

```bash
# Second page, 5 per page
curl "http://127.0.0.1:8000/customers?page=2&page_size=5"

# High-income women, richest first
curl "http://127.0.0.1:8000/customers?genre=female&min_income=100&sort_by=annual_income_k&order=desc"

# Search: numeric terms match id/age/income/score, text matches genre
curl "http://127.0.0.1:8000/customers/search?q=137"

# One customer / summary stats
curl "http://127.0.0.1:8000/customers/42"
curl "http://127.0.0.1:8000/stats"
```

Sample response (`/customers?genre=female&min_income=100&page_size=3`):

```json
{
  "items": [
    {"customer_id": 187, "genre": "Female", "age": 54, "annual_income_k": 101, "spending_score": 24},
    {"customer_id": 189, "genre": "Female", "age": 41, "annual_income_k": 103, "spending_score": 17},
    {"customer_id": 190, "genre": "Female", "age": 36, "annual_income_k": 103, "spending_score": 85}
  ],
  "page": 1,
  "page_size": 3,
  "total_items": 9,
  "total_pages": 3
}
```

## Validation & error handling

- Query/path parameters are validated by FastAPI (`422` with details on violation) —
  page bounds, score/age ranges, sort field and order whitelists.
- Inverted ranges (`min_age > max_age`) and unknown genres return a descriptive `422`.
- Unknown customer IDs return `404`.
- Hitting the API before running the import returns `503` with the exact command to fix it.
- All SQL is parameterised; `LIKE` search terms are escaped (`%`, `_`, `\`).

## Tests

```bash
python -m pytest tests/ -v
```

15 end-to-end tests build a throwaway database from the real CSV (via
`SHOPPING_DB_PATH`) and exercise listing, pagination, filtering, sorting,
search, validation failures, 404s and the stats endpoint.

> If pytest reports `PermissionError` on `%TEMP%\pytest-of-<user>` (a Windows ACL
> quirk), point it elsewhere: `python -m pytest tests/ --basetemp=.pytest-tmp`.

## Known limitations & future improvements

- **Read-only API** — no POST/PUT/DELETE; the dataset is treated as immutable input.
- **No authentication or rate limiting** — fine locally, required before real deployment.
- **SQLite** — perfect for this scale, but a concurrent multi-writer deployment would
  need PostgreSQL/MySQL and a migration tool (e.g. Alembic).
- **Basic search** — substring/exact matching only; no fuzzy matching or relevance ranking.
- **No CI pipeline** — tests run locally; a GitHub Actions workflow would run them per PR.
- **No containerisation** — a Dockerfile + compose file would make onboarding one command.
- **Stats are computed per request** — cheap at 200 rows; caching would matter at scale.
