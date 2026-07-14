
# Shopping Customer API

A small production-style, read-only REST API over the 200-row shopping customer dataset supplied through Google Drive. The application validates and imports the CSV into SQLite, starts with a persisted local database, and exposes OpenAPI documentation through FastAPI.

## Database design

The `customers` table uses the source `CustomerID` as a `TEXT` primary key so leading zeroes are preserved.

| Column | SQLite type | Rule |
| --- | --- | --- |
| `customer_id` | `TEXT` | Primary key, e.g. `0001` |
| `gender` | `TEXT` | `Male` or `Female` (the source calls this `Genre`) |
| `age` | `INTEGER` | 0â€“120 |
| `annual_income_kusd` | `INTEGER` | Non-negative, in thousands of dollars |
| `spending_score` | `INTEGER` | 1â€“100 |

Gender, age, annual income, and spending score are indexed for the supported filters. The schema and idempotent CSV upsert live in `app/database.py`. The generated `shopping.db` is intentionally ignored; it is recreated from the versioned CSV.

## Setup

Python 3.11 or newer is recommended.

```bash
cd shopping-api
python -m venv .venv
```

Activate the environment (`source .venv/bin/activate` on macOS/Linux or `.venv\Scripts\Activate.ps1` in PowerShell), then install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Import and run

The server imports the CSV automatically when its database is empty. To create or refresh the database explicitly:

```bash
python -m app.import_data
```

Run the development server:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive Swagger documentation is at `http://127.0.0.1:8000/docs`.

Set `SHOPPING_DATABASE_PATH` to store or test against another SQLite file.

## API usage

Health and imported record count:

```bash
curl http://127.0.0.1:8000/health
```

Paginated listing:

```bash
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"
```

Filters can be combined: `gender`, `age_min`, `age_max`, `income_min`, `income_max`, `score_min`, and `score_max`.

```bash
curl "http://127.0.0.1:8000/customers?gender=Female&age_max=35&score_min=70"
```

Case-insensitive substring search over customer ID or gender:

```bash
curl "http://127.0.0.1:8000/customers?q=0001"
```

Retrieve one customer:

```bash
curl http://127.0.0.1:8000/customers/0001
```

Invalid query ranges and malformed IDs return FastAPI `422` responses; unknown valid customer IDs return `404`.

## Tests

```bash
pytest -q
```

Tests build an isolated temporary database from the CSV and exercise filtering, pagination, search, and `404` handling.

## Known limitations and future improvements

- SQLite and synchronous queries are appropriate for a small local dataset, but not high-concurrency workloads.
- The API is read-only and has no authentication, authorization, rate limiting, or audit log.
- Search is a simple substring match over customer ID and gender; larger datasets would benefit from SQLite FTS or a search service.
- Data refresh is a local CSV upsert rather than a scheduled, versioned ingestion pipeline.
- Automated tests cover core behavior but not the full validation matrix or performance characteristics.

