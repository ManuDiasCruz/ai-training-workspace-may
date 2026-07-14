# 🛍️ Shopping API

A small, production-style backend that turns the **Mall Customers** shopping
dataset into a queryable REST API. The dataset is imported into a local SQLite
database and exposed through a [FastAPI](https://fastapi.tiangolo.com/)
application supporting listing, pagination, filtering, search, validation and
error handling.

> Branch: **`48-hi-shopping-api-dataset`**

---

## Project description

The source dataset (`data/Shopping_data.csv`, 200 records) describes mall
customers with the columns:

| CSV column                | Meaning                              |
| ------------------------- | ------------------------------------ |
| `CustomerID`              | Zero-padded business id, e.g. `0001` |
| `Genre`                   | Gender (`Male` / `Female`)           |
| `Age`                     | Age in years                         |
| `Annual Income (k$)`      | Annual income in thousands of USD    |
| `Spending Score (1-100)`  | Mall-assigned spending score, 1–100  |

The project:

1. **Reads** the dataset from CSV.
2. **Designs** a simple relational schema for it.
3. **Imports & persists** the records into a local SQLite database.
4. **Serves** them via a REST API with pagination, filtering and search.
5. Ships with **automated tests** covering the endpoints.

### Tech stack

- **FastAPI** — web framework + automatic OpenAPI/Swagger docs
- **SQLAlchemy 2.0** — ORM & schema definition
- **SQLite** — zero-config local database
- **Pydantic v2** — request/response validation
- **pytest** + **httpx** — automated API tests

---

## Database design

A single table, `customers`, models the dataset. A surrogate integer primary
key is used internally, while the dataset's `CustomerID` is kept as a unique
business key (as text, to preserve leading zeros).

| Column           | Type         | Notes                                                    |
| ---------------- | ------------ | -------------------------------------------------------- |
| `id`             | INTEGER PK   | Auto-increment surrogate key                             |
| `customer_id`    | TEXT         | Unique, indexed — dataset id (`"0001"`)                  |
| `gender`         | TEXT         | Indexed — `CHECK (gender IN ('Male','Female'))`          |
| `age`            | INTEGER      | Indexed — `CHECK (age >= 0)`                             |
| `annual_income`  | INTEGER      | Indexed — income in k$, `CHECK (annual_income >= 0)`     |
| `spending_score` | INTEGER      | Indexed — `CHECK (spending_score BETWEEN 1 AND 100)`     |

**Design notes**

- Every field the API filters or sorts on is **indexed**, keeping list queries
  fast as the dataset grows.
- **CHECK constraints** enforce data integrity at the database layer, in
  addition to the application-level validation in the import script and API.
- The database file is treated as a **build artifact** — it is git-ignored and
  regenerated deterministically from the CSV via the import script.

```
shopping-api/
├── app/
│   ├── config.py       # env-driven configuration
│   ├── database.py     # engine, session, declarative base
│   ├── models.py       # Customer ORM model (schema + constraints)
│   ├── schemas.py      # Pydantic request/response models
│   ├── crud.py         # query logic (filters, search, sort, stats)
│   └── main.py         # FastAPI app, routes, error handling
├── scripts/
│   └── import_data.py  # CSV -> SQLite importer (idempotent)
├── tests/
│   ├── conftest.py     # in-memory DB + TestClient fixtures
│   └── test_api.py     # automated API tests
├── data/
│   └── Shopping_data.csv
└── requirements.txt
```

---

## Setup instructions

> All commands are run from the `shopping-api/` directory. Requires **Python 3.11+**.

```bash
cd shopping-api

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# .venv\Scripts\Activate.ps1        # Windows (PowerShell)
# source .venv/bin/activate         # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt
```

---

## Execution steps

```bash
# 1. Create the database and import the dataset (idempotent)
python -m scripts.import_data
# -> Imported 200 customers ... into the database.

# 2. Run the API server
uvicorn app.main:app --reload
```

The API is now available at **http://127.0.0.1:8000**.

- Interactive docs (Swagger UI): **http://127.0.0.1:8000/docs**
- Alternative docs (ReDoc): **http://127.0.0.1:8000/redoc**

### Running the tests

```bash
pytest
# 14 passed
```

Tests seed an **isolated in-memory database** from the CSV, so they never
touch your local `shopping.db`.

---

## API usage examples

### Endpoints

| Method | Path                      | Description                                    |
| ------ | ------------------------- | ---------------------------------------------- |
| GET    | `/health`                 | Liveness probe                                 |
| GET    | `/customers`              | List customers (pagination, filtering, search) |
| GET    | `/customers/{customer_id}`| Fetch a single customer by id                  |
| GET    | `/stats`                  | Aggregate dataset statistics                   |

### `GET /customers` query parameters

| Parameter      | Type   | Default       | Description                                        |
| -------------- | ------ | ------------- | -------------------------------------------------- |
| `limit`        | int    | `20`          | Page size (1–100)                                  |
| `offset`       | int    | `0`           | Records to skip                                    |
| `gender`       | enum   | –             | `Male` or `Female`                                 |
| `min_age`      | int    | –             | Minimum age (inclusive)                            |
| `max_age`      | int    | –             | Maximum age (inclusive)                            |
| `min_income`   | int    | –             | Minimum annual income (k$)                         |
| `max_income`   | int    | –             | Maximum annual income (k$)                         |
| `min_spending` | int    | –             | Minimum spending score (1–100)                     |
| `max_spending` | int    | –             | Maximum spending score (1–100)                     |
| `search`       | string | –             | Case-insensitive match on `customer_id` / `gender` |
| `sort_by`      | enum   | `customer_id` | `customer_id`, `age`, `annual_income`, `spending_score` |
| `order`        | enum   | `asc`         | `asc` or `desc`                                    |

### Examples

**List with pagination**

```bash
curl "http://127.0.0.1:8000/customers?limit=2"
```
```json
{
  "meta": { "total": 200, "limit": 2, "offset": 0, "count": 2 },
  "items": [
    { "customer_id": "0001", "gender": "Male", "age": 19, "annual_income": 15, "spending_score": 39 },
    { "customer_id": "0002", "gender": "Male", "age": 21, "annual_income": 15, "spending_score": 81 }
  ]
}
```

**Filter + sort — top-spending female customers**

```bash
curl "http://127.0.0.1:8000/customers?gender=Female&min_spending=90&sort_by=spending_score&order=desc&limit=3"
```
```json
{
  "meta": { "total": 6, "limit": 3, "offset": 0, "count": 3 },
  "items": [
    { "customer_id": "0012", "gender": "Female", "age": 35, "annual_income": 19, "spending_score": 99 },
    { "customer_id": "0020", "gender": "Female", "age": 35, "annual_income": 23, "spending_score": 98 },
    { "customer_id": "0168", "gender": "Female", "age": 33, "annual_income": 86, "spending_score": 95 }
  ]
}
```

**Search**

```bash
curl "http://127.0.0.1:8000/customers?search=0199"
```

**Fetch a single customer**

```bash
curl "http://127.0.0.1:8000/customers/0007"
```
```json
{ "customer_id": "0007", "gender": "Female", "age": 35, "annual_income": 18, "spending_score": 6 }
```

**Dataset statistics**

```bash
curl "http://127.0.0.1:8000/stats"
```
```json
{
  "total_customers": 200,
  "gender_breakdown": { "Female": 112, "Male": 88 },
  "age": { "min": 18.0, "max": 70.0, "avg": 38.85 },
  "annual_income": { "min": 15.0, "max": 137.0, "avg": 60.56 },
  "spending_score": { "min": 1.0, "max": 99.0, "avg": 50.2 }
}
```

### Validation & error handling

- Unknown customer → **404** `{"detail": "Customer '9999' not found."}`
- Inverted range (e.g. `min_age > max_age`) → **422** with an explanatory message
- Out-of-bounds params (`limit > 100`, invalid `gender`, negative ages) → **422**
- Database not yet imported → **503** with instructions to run the importer

---

## Configuration

The app reads optional environment variables (sensible defaults shown):

| Variable                    | Default                     | Purpose                          |
| --------------------------- | --------------------------- | -------------------------------- |
| `SHOPPING_DATA_FILE`        | `data/Shopping_data.csv`    | Source CSV path                  |
| `SHOPPING_DB_PATH`          | `shopping.db`               | SQLite file location             |
| `SHOPPING_DATABASE_URL`     | `sqlite:///<SHOPPING_DB_PATH>` | Full SQLAlchemy URL           |
| `SHOPPING_DEFAULT_PAGE_SIZE`| `20`                        | Default page size                |
| `SHOPPING_MAX_PAGE_SIZE`    | `100`                       | Maximum allowed page size        |

---

## Known limitations & future improvements

- **Read-only API** — no create/update/delete endpoints; the dataset is static.
- **SQLite** — great for a local demo, but a single-file DB is not ideal for
  high-concurrency production use (Postgres would be the next step).
- **Basic search** — substring match over `customer_id`/`gender` only, since
  the dataset has no free-text fields (no full-text search / relevance ranking).
- **No authentication / rate limiting** — every endpoint is public.
- **Offset pagination** — simple but can be inefficient for very large offsets;
  keyset (cursor) pagination would scale better.
- **No migrations** — schema is created directly from the ORM models; a tool
  like Alembic would be needed once the schema evolves.

See the repository's GitHub Issues (tagged with this branch) for the tracked
follow-up work.
