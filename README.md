# Shopping Dataset API

A small production-style Python REST API for the shopping dataset supplied in Google Drive. The project imports the CSV into a local SQLite database and exposes read-only operations for listing customers, paginating results, filtering by relevant fields, searching across the small dataset, and returning summary statistics.

Branch: `model-e-task002/shopping-api-dataset`

## Dataset

The source dataset is `Shopping_data.csv` from the Drive file provided in the task. This branch includes a checked-in copy at `data/shopping.csv` for local import. It contains 200 customer records with these columns:

| Source column | Stored column | Type |
| --- | --- | --- |
| `CustomerID` | `customer_id` | text |
| `Genre` | `genre` | text |
| `Age` | `age` | integer |
| `Annual Income (k$)` | `annual_income_k` | integer |
| `Spending Score (1-100)` | `spending_score` | integer |

`customer_id` is stored as text so IDs like `0001` keep their leading zeroes.

## Database design

The database is a single denormalized SQLite table because the dataset is small, read-only, and every API query is centered on one logical entity.

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score >= 0 AND spending_score <= 100)
);
```

Additional indexes are created on:

- `genre`
- `age`
- `annual_income_k`
- `spending_score`

The schema is created in `app/database.py`. The importer in `app/import_data.py` validates headers and numeric ranges before persisting rows.

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execution steps

1. Import the CSV into SQLite:

   ```bash
   python -m app.import_data
   ```

   This creates `data/shopping.db`.

2. Start the API:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. Open the interactive docs at `http://localhost:8000/docs`.

Environment variables:

- `SHOPPING_CSV_PATH`: optional alternate CSV path.
- `SHOPPING_DB_PATH`: optional alternate SQLite database path.

## API usage examples

### Health check

```bash
curl http://localhost:8000/health
```

### List customers with pagination

```bash
curl "http://localhost:8000/customers?page=1&page_size=20"
```

### Filter customers

```bash
curl "http://localhost:8000/customers?genre=Female&min_age=20&max_age=40&min_income=50&max_spending_score=80"
```

Supported `/customers` query params:

- `page` and `page_size`
- `genre`
- `customer_id`
- `min_age` / `max_age`
- `min_income` / `max_income`
- `min_spending_score` / `max_spending_score`

### Fetch a single customer

```bash
curl http://localhost:8000/customers/0001
```

IDs `1` through `999` are normalized to the zero-padded dataset style internally, so `/customers/1` also returns customer `0001`.

### Basic search

```bash
curl "http://localhost:8000/search?q=Female&page=1&page_size=10"
```

Search matches against:

- `customer_id`
- `genre`
- `age`
- `annual_income_k`
- `spending_score`

### Summary statistics

```bash
curl http://localhost:8000/summary
```

This returns customer count, overall averages, and averages grouped by genre.

## Validation and error handling

- Numeric query params are range-checked with FastAPI / Pydantic (`page >= 1`, `0 <= spending_score <= 100`, etc.).
- Inverted ranges such as `min_age > max_age` return `400`.
- Unknown customer IDs return `404`.
- Invalid `genre` values return `400`.
- Blank search values return `422`.
- CSV import raises clear errors when headers or numeric ranges do not match the expected dataset shape.

## Tests

```bash
python -m pytest -q
```

The automated test suite imports the CSV into an isolated temporary SQLite database and covers pagination, filtering, search, customer lookup, summary stats, and error paths.

## Known limitations and future improvements

- The API is read-only; there are no write endpoints.
- Search is implemented with simple `LIKE` / `CAST(... AS TEXT)` clauses. SQLite FTS5 would be better if the dataset grew.
- SQLite is enough for local use and this dataset size, but a Postgres profile would be the next database step for concurrent workloads.
- There is no authentication, authorization, or rate limiting.
- There is no migration framework or structured observability layer yet.
