# Shopping Customer API

A small production-style, read-only REST API for exploring the 200-row shopping customer dataset supplied through Google Drive. The service validates and imports the CSV into SQLite, then exposes paginated listing, filtering, simple search, record lookup, health status, and interactive OpenAPI documentation.

## Dataset

The source file is `data/Shopping_data.csv`. Its columns map into API/database fields as follows:

| Source column | Database/API field | Type | Notes |
| --- | --- | --- | --- |
| `CustomerID` | `customer_id` | text | Primary key; text preserves leading zeroes |
| `Genre` | `gender` | text | Source uses `Male` and `Female`; renamed for clarity |
| `Age` | `age` | integer | Validated between 0 and 120 |
| `Annual Income (k$)` | `annual_income_k` | integer | Annual income in thousands of dollars |
| `Spending Score (1-100)` | `spending_score` | integer | Validated between 1 and 100 |

## Database design

SQLite keeps the project easy to run locally. `schema.sql` defines:

- `customers`: one row per customer, with `customer_id` as the primary key, database `CHECK` constraints, and indexes for gender, age, income, and spending-score filters.
- `import_runs`: audit metadata for each successful import, including source name, SHA-256 checksum, row count, and timestamp.

The importer validates the complete CSV before opening its write transaction. A successful import atomically replaces the customer snapshot and records the import run. The generated `data/shopping.db` is local runtime state and is intentionally ignored by Git.

## Setup

Requirements: Python 3.11 or newer.

```bash
cd 723-ch-shop-api
python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the application and test dependencies (either command is supported):

```bash
python -m pip install -e ".[dev]"
# or
python -m pip install -r requirements.txt
```

## Import and run

Import the bundled dataset into the default SQLite database:

```bash
python -m scripts.import_data
```

To import another compatible file, pass its path:

```bash
python -m scripts.import_data path/to/Shopping_data.csv
```

The database location can be overridden with `SHOPPING_DB_PATH`.

Start the API with automatic reload for local development:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI or `http://127.0.0.1:8000/redoc` for ReDoc.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service status, database name, and imported row count |
| `GET` | `/customers` | Paginated customer listing with filters and search |
| `GET` | `/customers/{customer_id}` | Exact customer lookup; returns 404 when absent |

`GET /customers` accepts:

- `page` (default `1`) and `page_size` (default `20`, maximum `100`)
- `gender` (`Male` or `Female`)
- `min_age`, `max_age`
- `min_income`, `max_income` (thousands of dollars)
- `min_spending_score`, `max_spending_score`
- `q`, a case-insensitive substring search over ID, gender, age, income, and score

Invalid parameter types, bounds, gender values, and inverted ranges return HTTP 422. Missing customers return HTTP 404. Unexpected SQLite errors are returned as HTTP 503 without exposing database details.

## Usage examples

```bash
# First page with five records
curl "http://127.0.0.1:8000/customers?page=1&page_size=5"

# High-spending female customers between ages 25 and 40
curl "http://127.0.0.1:8000/customers?gender=Female&min_age=25&max_age=40&min_spending_score=80"

# Simple search
curl "http://127.0.0.1:8000/customers?q=0007"

# Exact record
curl "http://127.0.0.1:8000/customers/0001"

# Health check
curl "http://127.0.0.1:8000/health"
```

Example paginated response:

```json
{
  "items": [
    {
      "customer_id": "0001",
      "gender": "Male",
      "age": 19,
      "annual_income_k": 15,
      "spending_score": 39
    }
  ],
  "page": 1,
  "page_size": 1,
  "total": 200,
  "total_pages": 200
}
```

## Tests

```bash
pytest
```

The API test imports all 200 source rows into an isolated temporary database and checks pagination, combined filtering/search, exact lookup, invalid-range validation, and 404 handling.

## Known limitations and future improvements

- SQLite is appropriate for this local read-heavy dataset but not a horizontally scaled, write-heavy deployment. A future version could use PostgreSQL and managed migrations.
- Search uses `LIKE` across a small table. Full-text search or a dedicated search service would be more appropriate for larger and richer datasets.
- The API is intentionally read-only and has no authentication, authorization, or rate limiting.
- The data contract reflects the source's two gender labels and does not infer or expand categories absent from the dataset.
- Production packaging could add a container image, CI checks, observability, and deployment manifests.

