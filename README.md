# Shopping Customer API

A small, production-style read-only REST API for exploring a 200-row shopping
customer dataset. It imports a validated CSV snapshot into SQLite and exposes
paginated customer listing, combined filters, basic search, record lookup, health
status, stable validation errors, and generated OpenAPI documentation.

The source snapshot is [`Shopping_data.csv` on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing).
The tracked copy is `data/shopping_customers.csv`; line endings were normalized
without altering the source values. Its SHA-256 after normalization is
`3cff17f7cbe2b12dc1780b316e9e3b50c4c9c528d758ac40d6a52e7bb1898544`.

## Dataset and database design

The CSV contains 200 customers with these columns:

| CSV field | SQLite/API field | Type | Observed range/values |
| --- | --- | --- | --- |
| `CustomerID` | `customer_id` | `TEXT` primary key | `0001`–`0200` |
| `Genre` | `genre` | `TEXT NOT NULL` | `Female`, `Male` |
| `Age` | `age` | `INTEGER NOT NULL` | 18–70 |
| `Annual Income (k$)` | `annual_income_k` | `INTEGER NOT NULL` | 15–137 |
| `Spending Score (1-100)` | `spending_score` | `INTEGER NOT NULL` | 1–99 |

`CustomerID` is stored as text so its leading zeros are preserved. The SQLite
schema adds checks for accepted `genre` values, ages from 0–120, non-negative
income, and scores from 1–100. Individual indexes on each filterable field support
the API's current query patterns. The importer validates every input row and all
customer ID uniqueness before replacing the database snapshot in one transaction.

The generated `data/shopping.db` is deliberately ignored. Recreating it from the
tracked source avoids committing binary state and makes the import repeatable.

## Setup

Prerequisites: Python 3.10 or newer.

```bash
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git switch shop-api-d81825df

python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Create or refresh the database explicitly:

```bash
python -m app.import_data
# Imported 200 customers into .../data/shopping.db
```

Custom locations can be supplied either as CLI arguments or environment variables:

```bash
python -m app.import_data --csv data/shopping_customers.csv --database data/shopping.db

export SHOP_API_CSV_PATH=data/shopping_customers.csv
export SHOP_API_DATABASE_PATH=data/shopping.db
```

## Run the API

```bash
uvicorn app.main:app --reload
```

The application creates the schema and imports the default CSV automatically when
the database is empty. Useful local URLs:

- API base: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## API

| Method and path | Description |
| --- | --- |
| `GET /health` | Health status and persisted customer row count |
| `GET /api/v1/customers` | Paginated customer list with optional filters/search |
| `GET /api/v1/customers/{customer_id}` | Single customer lookup; returns 404 if absent |

### List and paginate

```bash
curl 'http://127.0.0.1:8000/api/v1/customers?page=2&page_size=3'
```

Response:

```json
{
  "items": [
    {
      "customer_id": "0004",
      "genre": "Female",
      "age": 23,
      "annual_income_k": 16,
      "spending_score": 77
    },
    {
      "customer_id": "0005",
      "genre": "Female",
      "age": 31,
      "annual_income_k": 17,
      "spending_score": 40
    },
    {
      "customer_id": "0006",
      "genre": "Female",
      "age": 22,
      "annual_income_k": 17,
      "spending_score": 76
    }
  ],
  "total": 200,
  "page": 2,
  "page_size": 3,
  "pages": 67
}
```

`page` defaults to 1. `page_size` defaults to 20 and accepts 1–100. Empty pages
are valid and return an empty `items` array with the requested page metadata.

### Filters and search

All filters are optional and can be combined:

| Parameter | Validation and behavior |
| --- | --- |
| `genre` | Case-insensitive exact `male` or `female` |
| `min_age`, `max_age` | Inclusive integer range, each 0–120 |
| `min_income`, `max_income` | Inclusive non-negative integer range in k$ |
| `min_spending_score`, `max_spending_score` | Inclusive integer range, each 1–100 |
| `q` | Case-insensitive substring match on customer ID or genre, 1–50 characters |

For example, find male customers with income of at least 120 k$, a spending score
of at least 70, and a customer ID containing `020`:

```bash
curl 'http://127.0.0.1:8000/api/v1/customers?genre=male&min_income=120&min_spending_score=70&q=020'
```

Find customers in a bounded age and score range:

```bash
curl 'http://127.0.0.1:8000/api/v1/customers?min_age=25&max_age=35&min_spending_score=80&page_size=50'
```

Get one original CSV record:

```bash
curl 'http://127.0.0.1:8000/api/v1/customers/0001'
```

Invalid parameter types/ranges return HTTP 422 in a consistent `{"detail": "..."}`
shape. Inverted ranges such as `min_age=50&max_age=30` return HTTP 400, and missing
customers return HTTP 404. SQL query values are passed as bound parameters.

## Automated tests

```bash
pytest -q
```

The suite uses a disposable SQLite database and exercises import-on-startup,
health metadata, stable ordering/pagination, combined filters and search, record
retrieval, not-found responses, and filter validation. It does not modify the
development database.

## Project structure

```text
app/
  config.py       Environment-aware file paths
  database.py     SQLite schema, connections, and table initialization
  import_data.py  CSV parsing, validation, and atomic snapshot replacement
  main.py         Application factory, API lifecycle, routes, and errors
  models.py       Pydantic response contracts
  repository.py   Bound-parameter read queries and filters
data/
  shopping_customers.csv
tests/
  conftest.py
  test_api.py
```

## Known limitations and future improvements

- SQLite and startup seeding suit a single-process local service and this small,
  static dataset. Use PostgreSQL, versioned migrations, and an explicit ingestion
  job before horizontally scaling or accepting frequent source updates.
- Search intentionally covers only customer ID and genre. Full-text search is
  unnecessary for the current five-column dataset, but a larger customer/product
  source would benefit from normalized entities, searchable descriptive fields,
  sortable results, and aggregate analytics endpoints.
- The API is read-only and has no authentication, rate limiting, or tenant/data
  access controls. Add these before exposing customer-linked data outside a
  trusted local network.
- There is no CI/CD pipeline or container packaging yet. Automated linting,
  dependency/security scanning, tests, reproducible images, and a deployment
  health check should be required before releases.

These items are tracked as separate repository issues associated with branch
`shop-api-d81825df`.
