# Shopping Dataset REST API

A small, production-style backend that exposes the classic **mall shopping
dataset** over a REST API. The dataset is imported into a local SQLite database
and served through a [FastAPI](https://fastapi.tiangolo.com/) application with
pagination, filtering, free-text search, input validation and error handling.

> Branch: `medium-shopping-api-dataset`

---

## Project description

The source data (`data/Shopping_data.csv`, 200 records) describes mall
customers with the following columns:

| Column                   | Meaning                              |
| ------------------------ | ------------------------------------ |
| `CustomerID`             | Zero-padded customer identifier      |
| `Genre`                  | `Male` / `Female`                    |
| `Age`                    | Customer age in years                |
| `Annual Income (k$)`     | Annual income in thousands of USD    |
| `Spending Score (1-100)` | Mall-assigned spending score (1–100) |

The API lets you list, paginate, filter, search and aggregate these records, as
well as fetch a single customer by id.

---

## Database design

A single SQLite table, `customers`, mirrors the dataset one-to-one. SQLite was
chosen because it is file-based, requires no server, and keeps the project fully
runnable locally with zero external infrastructure.

| Column           | Type    | Constraints                                  | Notes                                        |
| ---------------- | ------- | -------------------------------------------- | -------------------------------------------- |
| `customer_id`    | TEXT    | **PRIMARY KEY**, indexed                     | Stored as `"0001"` to preserve leading zeros |
| `genre`          | TEXT    | NOT NULL, indexed, `IN ('Male','Female')`    |                                              |
| `age`            | INTEGER | NOT NULL, indexed, `>= 0`                    |                                              |
| `annual_income`  | INTEGER | NOT NULL, indexed, `>= 0`                    | In thousands of dollars (k$)                 |
| `spending_score` | INTEGER | NOT NULL, indexed, `BETWEEN 1 AND 100`       |                                              |

Design notes:

- **`customer_id` as TEXT** preserves the original zero-padded identifiers
  exactly (`0001`, `0042`, …) instead of collapsing them to integers.
- **`CHECK` constraints** enforce data integrity at the database level, in
  addition to Pydantic validation at the API layer (defense in depth).
- **Indexes** on every queryable column keep filtering and sorting fast.
- The schema is defined with SQLAlchemy ORM models (`app/models.py`) so the same
  definitions drive both the import script and the API.

The import (`scripts/import_data.py`) is **idempotent**: it drops and recreates
the schema, then bulk-loads the CSV, so re-running always yields a clean dataset.

---

## Project structure

```
shopping-api/
├── app/
│   ├── database.py     # SQLite engine, session, declarative base
│   ├── models.py       # Customer ORM model + constraints
│   ├── schemas.py      # Pydantic request/response models
│   ├── crud.py         # Shared query builder (filter/search/sort/stats)
│   └── main.py         # FastAPI app and route definitions
├── data/
│   └── Shopping_data.csv
├── scripts/
│   └── import_data.py  # CSV -> SQLite loader (idempotent)
├── tests/
│   └── test_api.py     # Automated API tests (pytest)
├── requirements.txt
└── README.md
```

---

## Setup instructions

Requires **Python 3.10+**.

```bash
cd shopping-api

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate     # Windows (Git Bash)
# source .venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Import the dataset into the local SQLite database (creates shopping.db)
python -m scripts.import_data
```

---

## Execution steps

Run the API server with uvicorn:

```bash
uvicorn app.main:app --reload
```

Then open:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc:      <http://127.0.0.1:8000/redoc>
- Health:     <http://127.0.0.1:8000/health>

Run the automated tests:

```bash
pytest
```

---

## API usage examples

### Endpoints

| Method & path             | Description                                            |
| ------------------------- | ------------------------------------------------------ |
| `GET /health`             | Liveness probe                                         |
| `GET /customers`          | List with pagination, filtering, search and sorting    |
| `GET /customers/stats`    | Aggregate statistics (respects the same filters)       |
| `GET /customers/{id}`     | Fetch a single customer by id                          |

### List & paginate

```bash
curl "http://127.0.0.1:8000/customers?limit=5&offset=10"
```

```json
{
  "total": 200,
  "limit": 5,
  "offset": 10,
  "count": 5,
  "items": [ { "customer_id": "0011", "genre": "Male", "age": 67, "annual_income": 19, "spending_score": 14 }, ... ]
}
```

### Filter by relevant fields

```bash
# Female customers aged 30–40 with income between 50k and 70k
curl "http://127.0.0.1:8000/customers?genre=Female&min_age=30&max_age=40&min_income=50&max_income=70"

# High spenders, highest first
curl "http://127.0.0.1:8000/customers?min_spending_score=90&sort_by=spending_score&order=desc"
```

Supported filters: `genre`, `min_age`, `max_age`, `min_income`, `max_income`,
`min_spending_score`, `max_spending_score`.
Sorting: `sort_by` ∈ {`customer_id`, `age`, `annual_income`, `spending_score`},
`order` ∈ {`asc`, `desc`}.

### Search

Free-text search across id, genre and numeric columns:

```bash
curl "http://127.0.0.1:8000/customers?search=137"   # matches income 137 -> customers 0199, 0200
curl "http://127.0.0.1:8000/customers?search=Female"
```

### Single customer

```bash
curl "http://127.0.0.1:8000/customers/0042"
```

### Statistics

```bash
curl "http://127.0.0.1:8000/customers/stats?genre=Male"
```

```json
{
  "total": 88,
  "avg_age": 39.81,
  "avg_annual_income": 62.23,
  "avg_spending_score": 48.51,
  "genre_breakdown": { "Male": 88 }
}
```

### Validation & error handling

- Invalid enum/range values return **422** with a descriptive message
  (e.g. `genre=Other`, `limit=1000`, or `min_age > max_age`).
- Unknown customer ids return **404** with `{"detail": "Customer '9999' not found"}`.
- Unhandled server errors return a safe **500** JSON response.

---

## Known limitations & future improvements

- **Read-only API** — there are no create/update/delete endpoints; the dataset is
  treated as immutable reference data.
- **SQLite** is great for local use but not ideal for high-concurrency
  production; a Postgres backend would be the next step.
- **Search is `LIKE`-based** (substring match). A proper full-text or fuzzy
  search index would scale and rank better.
- **No authentication / rate limiting** — the API is open.
- **No pre-computed aggregates / caching** — stats are computed per request.
- See the repository issues tagged with this branch for detailed next steps.
