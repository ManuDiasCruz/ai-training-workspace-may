# ShopAPI — Shopping Dataset REST API

A small production-style backend that imports the mall customers shopping
dataset (200 records) into a local SQLite database and exposes it through a
FastAPI REST service with pagination, filtering, search, and summary
statistics.

> Branch: `731-fa-h-shopapi` — everything for this project lives in the
> `shopapi/` directory.

## Dataset

`data/Shopping_data.csv` (sourced from Google Drive) contains 200 mall
customers with the columns:

| CSV column               | Meaning                                  |
| ------------------------ | ---------------------------------------- |
| `CustomerID`             | Unique customer identifier (0001–0200)   |
| `Genre`                  | Customer gender (`Male` / `Female`)      |
| `Age`                    | Customer age in years                    |
| `Annual Income (k$)`     | Annual income in thousands of dollars    |
| `Spending Score (1-100)` | Mall-assigned spending score             |

## Database design

SQLite, single table (`data/shopping.db`, created by the import script):

```sql
CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
```

Design notes:

- The dataset is a single flat entity, so one table is the honest model — no
  artificial normalization.
- `CHECK` constraints enforce data integrity at the database layer, mirroring
  the validation done at import time and in the API layer.
- Indexes on `genre`, `age`, `annual_income_k`, and `spending_score` support
  the API's filter queries.
- The DB path can be overridden with the `SHOPAPI_DB` environment variable
  (used by the test suite to run against a throwaway database).

## Setup

Requires Python 3.10+.

```bash
cd shopapi
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Running

1. **Import the dataset** (creates `data/shopping.db`, idempotent — reruns
   replace the data):

   ```bash
   python -m app.import_data
   ```

2. **Start the API**:

   ```bash
   uvicorn app.main:app --reload
   ```

3. Open the interactive docs at <http://127.0.0.1:8000/docs>.

## Running the tests

```bash
python -m pytest
```

The 13 tests spin up the app against a temporary database seeded from the
real CSV and cover listing, pagination, filtering, sorting, search, detail
lookup, statistics, and validation/error paths.

## API endpoints

| Method | Path                | Description                                     |
| ------ | ------------------- | ----------------------------------------------- |
| GET    | `/health`           | Service health + row count                      |
| GET    | `/customers`        | List customers (pagination, filters, sorting)   |
| GET    | `/customers/{id}`   | Fetch one customer by ID (404 if missing)       |
| GET    | `/customers/search` | Search by customer ID (numeric) or genre (text) |
| GET    | `/stats/summary`    | Aggregate statistics, overall and per genre     |

### Query parameters for `/customers`

- `page` (default 1), `page_size` (default 20, max 100)
- `genre` — `Male` or `Female`
- `min_age` / `max_age` (1–120)
- `min_income` / `max_income` (k$, ≥ 0)
- `min_score` / `max_score` (1–100)
- `sort_by` — `customer_id` | `age` | `annual_income_k` | `spending_score`
- `order` — `asc` | `desc`

Inverted ranges (e.g. `min_age=50&max_age=20`) return `400`; out-of-bounds or
malformed parameters return `422` with details.

### Examples

```bash
# Second page, 50 per page
curl "http://127.0.0.1:8000/customers?page=2&page_size=50"

# High-income male customers, biggest spenders first
curl "http://127.0.0.1:8000/customers?genre=Male&min_income=100&sort_by=spending_score&order=desc"

# Customers aged 30-40
curl "http://127.0.0.1:8000/customers?min_age=30&max_age=40"

# One customer
curl "http://127.0.0.1:8000/customers/42"

# Search: numeric query matches ID, text query matches genre
curl "http://127.0.0.1:8000/customers/search?q=42"
curl "http://127.0.0.1:8000/customers/search?q=female"

# Summary statistics
curl "http://127.0.0.1:8000/stats/summary"
```

Sample `/customers` response:

```json
{
  "items": [
    {"customer_id": 1, "genre": "Male", "age": 19, "annual_income_k": 15, "spending_score": 39}
  ],
  "total": 200,
  "page": 1,
  "page_size": 20,
  "pages": 10
}
```

## Known limitations / future improvements

- **Read-only API** — no create/update/delete endpoints; the dataset is
  static after import.
- **Limited search** — the dataset has no free-text fields, so search only
  covers customer ID and genre.
- **SQLite** — perfect for a local single-user service, but a client/server
  database (PostgreSQL) would be needed for concurrent writes or scale.
- **No auth or rate limiting** — endpoints are open; production use would
  need API keys/OAuth and throttling.
- **No CI pipeline** — tests run locally; a GitHub Actions workflow would
  automate them per push.
- **No containerization** — a Dockerfile would make setup one command.
- Analytics could go further: percentiles, age-band buckets, or customer
  segmentation (e.g. k-means on income × spending score).
