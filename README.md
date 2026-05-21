# Shopping Dataset API

Branch: `model-g-task002/sad`

This project is a small FastAPI backend for the shopping dataset provided in Google Drive as `Shopping_data.csv`. It imports the CSV into a local SQLite database and exposes REST endpoints for listing records, pagination, filtering, sorting, search, summary statistics, and basic customer maintenance.

## Dataset

The Drive file contains 200 customer records with these columns:

| Source column | Stored field | Type | Notes |
| --- | --- | --- | --- |
| `CustomerID` | `customer_code` | string | Preserves zero-padded IDs such as `0001`. |
| `Genre` | `gender` | string | Expected values are `Male` or `Female`. |
| `Age` | `age` | integer | Validated from 0 to 130. |
| `Annual Income (k$)` | `annual_income_k` | integer | Annual income in thousands of dollars. |
| `Spending Score (1-100)` | `spending_score` | integer | Validated from 1 to 100. |

The source CSV is stored at `data/Shopping_data.csv` so the API can be run locally without requiring Drive access at runtime.

## Database Design

The application uses SQLite through SQLAlchemy. By default, the database is created as `shopping.db` in the project root. You can override this with `DATABASE_URL`.

The schema is a single `customers` table because the dataset is small and each row describes one customer:

```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    customer_code VARCHAR(8) NOT NULL UNIQUE,
    gender VARCHAR(16) NOT NULL,
    age INTEGER NOT NULL,
    annual_income_k INTEGER NOT NULL,
    spending_score INTEGER NOT NULL,
    CONSTRAINT ck_customer_age_range CHECK (age >= 0 AND age <= 130),
    CONSTRAINT ck_customer_income_nonneg CHECK (annual_income_k >= 0),
    CONSTRAINT ck_customer_spending_range CHECK (spending_score >= 1 AND spending_score <= 100)
);
```

Indexes are defined for `id`, `customer_code`, and the combined `gender, age` lookup path.

## Setup

Requires Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execution

Import the dataset into SQLite:

```bash
python -m scripts.import_data
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Open the interactive API docs at:

```text
http://localhost:8000/docs
```

Run tests:

```bash
python -m pytest -q
```

## API Usage

Health check:

```bash
curl http://localhost:8000/health
```

Summary statistics:

```bash
curl http://localhost:8000/stats
```

List customers with pagination:

```bash
curl "http://localhost:8000/customers?page=1&page_size=20"
```

Filter records:

```bash
curl "http://localhost:8000/customers?gender=Female&min_age=20&max_age=40&min_income=40&max_score=80"
```

Search across customer code, gender, age, income, and spending score:

```bash
curl "http://localhost:8000/customers?search=137&page_size=50"
```

Sort records:

```bash
curl "http://localhost:8000/customers?sort_by=spending_score&order=desc&page_size=10"
```

Fetch one customer by internal database ID:

```bash
curl http://localhost:8000/customers/1
```

Create a customer:

```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"customer_code":"9999","gender":"Female","age":28,"annual_income_k":60,"spending_score":55}'
```

Delete a customer:

```bash
curl -X DELETE http://localhost:8000/customers/201
```

## Validation and Error Handling

- Query parameters are validated with FastAPI and Pydantic.
- Invalid ranges such as `min_age > max_age` return `400`.
- Blank search values return `400`.
- Missing customers return `404`.
- Duplicate `customer_code` values return `409`.
- CSV import validates headers and row-level numeric ranges before committing data.

## Known Limitations and Future Improvements

- The database is local SQLite only; a Postgres profile would be better for concurrent or deployed environments.
- The import process reads the checked-in CSV; it does not automatically download from Google Drive.
- Search uses simple SQL `LIKE` matching; SQLite FTS5 would scale better for richer search.
- There is no authentication, authorization, or rate limiting.
- There is no migration framework, so schema changes are managed directly through SQLAlchemy model metadata.
- Observability is minimal; structured logs and request metrics would be useful before production deployment.
