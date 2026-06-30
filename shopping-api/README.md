# Shopping Dataset REST API

A small, production-style backend API built over the **mall shopping dataset**
(customer demographics, annual income and spending score). It demonstrates a
clean path from a raw CSV to a documented, tested, runnable REST service.

> **Branch:** `low-shopping-api-dataset`

## Project Description

The dataset (`data/Shopping_data.csv`, 200 records) contains one row per mall
customer with the following columns:

| CSV column                | Meaning                                  |
| ------------------------- | ---------------------------------------- |
| `CustomerID`              | Unique customer identifier (1–200)       |
| `Genre`                   | Gender (`Male` / `Female`)               |
| `Age`                     | Age in years                             |
| `Annual Income (k$)`      | Annual income in thousands of dollars    |
| `Spending Score (1-100)`  | Mall-assigned spending score (1–100)     |

The service:

- reads and persists the dataset into a local **SQLite** database,
- exposes a **FastAPI** REST API for listing, pagination, filtering, search and
  aggregate statistics,
- validates input and returns meaningful error responses,
- ships with an automated test suite.

## Tech Stack

- **Python 3.12**
- **FastAPI** + **Uvicorn** (web framework / ASGI server)
- **SQLAlchemy 2.x** (ORM)
- **SQLite** (zero-config local database)
- **Pydantic v2** (validation / serialization)
- **pytest** + Starlette `TestClient` (tests)

## Database Design

A single table, `customers`, maps directly onto the CSV. `CustomerID` is the
natural primary key. Indexed columns support the filter/search/sort operations.

| Column            | Type    | Notes                                      |
| ----------------- | ------- | ------------------------------------------ |
| `customer_id`     | INTEGER | Primary key (from `CustomerID`)            |
| `genre`           | TEXT    | Indexed; `CHECK` in (`Male`, `Female`)     |
| `age`             | INTEGER | Indexed; `CHECK >= 0`                       |
| `annual_income_k` | INTEGER | Indexed; `CHECK >= 0`                       |
| `spending_score`  | INTEGER | Indexed; `CHECK BETWEEN 1 AND 100`         |

Design notes:

- A single denormalized table is appropriate here — the dataset is flat, small
  and has no relational structure to normalize.
- `CHECK` constraints enforce data integrity at the storage layer in addition to
  API-level validation.
- Per-column indexes keep the filter, search and sort endpoints fast.

## Project Structure

```
shopping-api/
├── app/
│   ├── database.py      # engine, session, declarative base
│   ├── models.py        # Customer ORM model + constraints
│   ├── schemas.py       # Pydantic request/response models
│   ├── crud.py          # query / filter / pagination / stats logic
│   └── main.py          # FastAPI app and endpoints
├── data/
│   └── Shopping_data.csv
├── scripts/
│   └── import_data.py   # CSV -> SQLite loader (idempotent)
├── tests/
│   └── test_api.py      # automated API tests
├── requirements.txt
└── README.md
```

## Setup Instructions

```bash
cd shopping-api

# 1. Create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Execution Steps

```bash
# 1. Import the dataset into the local SQLite database (creates shopping.db)
python -m scripts.import_data

# 2. Run the API server
uvicorn app.main:app --reload

# 3. Open the interactive docs
#    http://127.0.0.1:8000/docs
```

Run the tests:

```bash
pytest -q
```

## API Endpoints

| Method | Path                          | Description                              |
| ------ | ----------------------------- | ---------------------------------------- |
| GET    | `/health`                     | Liveness probe                           |
| GET    | `/customers`                  | List with pagination/filter/search/sort  |
| GET    | `/customers/{customer_id}`    | Fetch a single customer by id            |
| GET    | `/customers/stats/summary`    | Aggregate statistics (respects filters)  |

### `GET /customers` query parameters

| Parameter            | Type   | Default       | Description                                  |
| -------------------- | ------ | ------------- | -------------------------------------------- |
| `limit`              | int    | `20`          | Page size (1–200)                            |
| `offset`             | int    | `0`           | Records to skip                              |
| `sort_by`            | str    | `customer_id` | `customer_id` \| `age` \| `annual_income_k` \| `spending_score` |
| `order`              | str    | `asc`         | `asc` \| `desc`                              |
| `genre`              | str    | –             | `Male` / `Female` (case-insensitive)         |
| `min_age` / `max_age`| int    | –             | Age range (inclusive)                        |
| `min_income` / `max_income` | int | –        | Annual income range (k$, inclusive)          |
| `min_spending_score` / `max_spending_score` | int | – | Spending score range (1–100)        |
| `search`             | str    | –             | Free-text across genre and customer id       |

## API Usage Examples

```bash
# Health check
curl http://127.0.0.1:8000/health

# First page of customers
curl "http://127.0.0.1:8000/customers?limit=5"

# Pagination
curl "http://127.0.0.1:8000/customers?limit=10&offset=20"

# Filter: female customers with a high spending score, sorted by income desc
curl "http://127.0.0.1:8000/customers?genre=Female&min_spending_score=80&sort_by=annual_income_k&order=desc"

# Filter by income range
curl "http://127.0.0.1:8000/customers?min_income=50&max_income=80"

# Search (matches genre or customer id substring)
curl "http://127.0.0.1:8000/customers?search=fem"

# Single customer
curl http://127.0.0.1:8000/customers/1

# Aggregate statistics (also honors filters)
curl "http://127.0.0.1:8000/customers/stats/summary?genre=Male"
```

Example response from `/customers?limit=2`:

```json
{
  "total": 200,
  "limit": 2,
  "offset": 0,
  "count": 2,
  "items": [
    {"customer_id": 1, "genre": "Male", "age": 19, "annual_income_k": 15, "spending_score": 39},
    {"customer_id": 2, "genre": "Male", "age": 21, "annual_income_k": 15, "spending_score": 81}
  ]
}
```

## Input Validation & Error Handling

- Query parameters are bounded with FastAPI `Query` constraints (`ge`, `le`,
  regex patterns) — invalid values return **422**.
- Cross-field checks (e.g. `min_age > max_age`, unknown `genre`) return **422**
  with a descriptive message.
- Unknown customer ids return **404**.
- `CHECK` constraints enforce integrity at the database layer.

## Known Limitations & Future Improvements

- **Read-only API** — no create/update/delete endpoints yet.
- **Substring search only** — `search` is a simple `LIKE` over genre/id; there
  is no full-text or fuzzy search.
- **SQLite / single-node** — fine for this dataset, but not suited to high
  concurrency or large data volumes.
- **No authentication / rate limiting.**
- **Offset pagination** — simple but degrades for very large offsets; cursor
  pagination would scale better.
- **No clustering/segmentation** — the dataset is commonly used for customer
  segmentation (e.g. K-means); an analytics endpoint could expose that.

See the GitHub issues opened for this branch for concrete next steps.
