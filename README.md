# Shopping Customer API

Small FastAPI backend for exploring the shopping customer dataset from Google Drive. The service imports the CSV into a local SQLite database and exposes read-only REST endpoints for listing, pagination, filtering, search, lookup, and dataset stats.

## Dataset

Source file: `Shopping_data.csv`

Columns inspected:

| CSV column | API/database field | Type | Notes |
| --- | --- | --- | --- |
| `CustomerID` | `customer_id` | text | Four digit customer id, primary key |
| `Genre` | `genre` | text | `Male` or `Female` |
| `Age` | `age` | integer | Observed range: 18-70 |
| `Annual Income (k$)` | `annual_income_k` | integer | Observed range: 15-137 |
| `Spending Score (1-100)` | `spending_score` | integer | Observed range: 1-99 |

The committed CSV contains 200 customer records. The generated SQLite database is intentionally ignored because it is reproducible from the CSV.

## Database Design

SQLite database path: `data/shopping.db`

Single-table schema:

```sql
CREATE TABLE shopping_customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
```

Indexes are created on `genre`, `age`, `annual_income_k`, and `spending_score` to support the common filters exposed by the API.

## Setup

Requires Python 3.10, 3.11, or 3.12.

Using `uv`:

```bash
uv sync --python 3.10 --extra dev
```

Using `venv` and `pip`:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Import The Dataset

The API auto-creates and imports the database on startup when `data/shopping.db` is missing or empty. To run the import explicitly:

```bash
uv run python -m app.import_data --csv data/Shopping_data.csv --db data/shopping.db
```

Expected output:

```text
Imported 200 customer records into data/shopping.db
```

Environment overrides are available:

| Variable | Purpose |
| --- | --- |
| `SHOPPING_API_DB_PATH` | Override SQLite database path |
| `SHOPPING_API_CSV_PATH` | Override source CSV path |

## Run The API

```bash
uv run uvicorn app.main:app --reload
```

Default URL: `http://127.0.0.1:8000`

Interactive docs are available at `/docs`.

## API Examples

Health check:

```bash
curl http://127.0.0.1:8000/health
```

List customers with pagination:

```bash
curl "http://127.0.0.1:8000/customers?page=1&per_page=10"
```

Filter by genre, age, and spending score:

```bash
curl "http://127.0.0.1:8000/customers?genre=Female&min_age=20&max_age=40&min_spending_score=70"
```

Search across id, genre, age, income, and spending score:

```bash
curl "http://127.0.0.1:8000/customers?q=0001"
```

Sort a page by income descending:

```bash
curl "http://127.0.0.1:8000/customers?sort_by=annual_income_k&sort_order=desc&per_page=5"
```

Fetch one customer:

```bash
curl http://127.0.0.1:8000/customers/0001
```

Dataset stats:

```bash
curl http://127.0.0.1:8000/stats
```

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Service/database health check |
| `GET` | `/customers` | List records with pagination, filtering, search, and sorting |
| `GET` | `/customers/{customer_id}` | Fetch one customer by id |
| `GET` | `/stats` | Return dataset counts and min/max ranges |

Supported `/customers` query parameters:

| Parameter | Description |
| --- | --- |
| `page` | One-based page number, minimum `1` |
| `per_page` | Page size, `1` to `100` |
| `genre` | `Male` or `Female` |
| `min_age`, `max_age` | Age range |
| `min_income`, `max_income` | Annual income range in thousands |
| `min_spending_score`, `max_spending_score` | Spending score range |
| `q` | Case-insensitive basic search |
| `sort_by` | `customer_id`, `age`, `annual_income_k`, or `spending_score` |
| `sort_order` | `asc` or `desc` |

Errors return a consistent shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": []
  }
}
```

## Tests

Run:

```bash
uv run pytest
```

Current tests cover the registered API route handlers for listing/filtering/search pagination, customer lookup, not-found handling, and invalid range validation.

## Known Limitations And Future Improvements

- The API is read-only; there are no create, update, or delete endpoints.
- Search is simple `LIKE` matching, which is fine for 200 rows but should become SQLite FTS or external search for larger datasets.
- The dataset is a static snapshot from Drive; there is no scheduled sync or data provenance table.
- SQLite is appropriate for local development, but a managed database and migration tooling would be better for multi-user production deployments.
- Authentication, rate limiting, request tracing, and structured logging are not implemented.

