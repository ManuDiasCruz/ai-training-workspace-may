# Shopping Customers API

A small production-style Python REST API built on top of the **Mall Customers**
shopping dataset (`data/Shopping_data.csv`, 200 rows). The API exposes paginated
listing, filtering, search, basic CRUD, and aggregate stats over the dataset.

Branch: `model-c-task002/shopping-api-dataset`

## Project description

The project is a self-contained backend service that:

1. Reads the shopping dataset (CSV) and imports it into a local SQLite database.
2. Exposes a JSON REST API (FastAPI) with pagination, filters, search and CRUD.
3. Ships with an automated test suite (`pytest`) that runs against an isolated DB.

It is intentionally small and easy to run locally — no external services, no
container required.

## Dataset

```
CustomerID, Genre, Age, Annual Income (k$), Spending Score (1-100)
```

- 200 rows
- `Genre`: `Male` / `Female`
- `Age`: integer years
- `Annual Income (k$)`: integer, thousands of USD
- `Spending Score (1-100)`: integer 1..100

## Database design

A single relational table, `customers`, modelled with SQLAlchemy 2.x:

| column            | type        | constraints                          |
| ----------------- | ----------- | ------------------------------------ |
| `customer_id`     | INTEGER PK  | from CSV, also auto-extendable       |
| `genre`           | VARCHAR(16) | `NOT NULL`, indexed                  |
| `age`             | INTEGER     | `NOT NULL`, `>= 0`                   |
| `annual_income_k` | INTEGER     | `NOT NULL`, `>= 0`, indexed          |
| `spending_score`  | INTEGER     | `NOT NULL`, `BETWEEN 1 AND 100`, idx |

Indexes on `genre`, `age`, `annual_income_k`, and `spending_score` keep the
filter and sort queries cheap. The schema is created automatically the first
time the importer or the API starts (`init_db()` in `app/db.py`).

The DB file lives at `./shopping.db` (SQLite). Override with
`SHOPPING_DATABASE_URL` if you want to point at a different database.

## Project layout

```
app/
  __init__.py
  db.py          # SQLAlchemy engine, Base, get_db dependency
  models.py      # Customer ORM model
  schemas.py     # Pydantic request/response models
  crud.py        # query helpers and CRUD ops
  importer.py    # CSV → SQLite loader (CLI)
  main.py        # FastAPI app and routes
tests/
  conftest.py    # isolated test DB + dependency override
  test_api.py    # 15 API tests
data/
  Shopping_data.csv
requirements.txt
```

## Setup

```bash
# 1. (optional) create a virtual env
python3 -m venv .venv && source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. import the dataset into ./shopping.db
python -m app.importer

# 4. run the API
uvicorn app.main:app --reload
```

The server starts on http://127.0.0.1:8000. Interactive docs are at
http://127.0.0.1:8000/docs.

## Running the tests

```bash
pytest -v
```

Each test runs against a fresh SQLite database in `tmp_path` seeded from the
CSV — production data is never mutated.

## API endpoints

| method | path                       | description                                |
| ------ | -------------------------- | ------------------------------------------ |
| GET    | `/health`                  | liveness probe                             |
| GET    | `/stats`                   | dataset aggregates (counts, min/max/avg)   |
| GET    | `/customers`               | list with pagination, filters, search, sort |
| GET    | `/customers/{customer_id}` | get one customer                           |
| POST   | `/customers`               | create a customer                          |
| PATCH  | `/customers/{customer_id}` | partial update                             |
| DELETE | `/customers/{customer_id}` | delete a customer                          |

### `GET /customers` query parameters

| param        | type | notes                                                     |
| ------------ | ---- | --------------------------------------------------------- |
| `limit`      | int  | 1..500, default 50                                        |
| `offset`     | int  | >=0, default 0                                            |
| `genre`      | str  | `Male` / `Female`, case-insensitive                       |
| `min_age`    | int  | 0..150                                                    |
| `max_age`    | int  | 0..150                                                    |
| `min_income` | int  | thousands of USD                                          |
| `max_income` | int  | thousands of USD                                          |
| `min_score`  | int  | 1..100                                                    |
| `max_score`  | int  | 1..100                                                    |
| `search`     | str  | substring match against `genre` and stringified `id`      |
| `sort_by`    | str  | `customer_id` / `age` / `annual_income_k` / `spending_score` |
| `sort_order` | str  | `asc` / `desc`                                            |

Inconsistent ranges (e.g. `min_age=60&max_age=20`) return `400`.

## API usage examples

```bash
# Aggregate stats
curl -s http://127.0.0.1:8000/stats | jq .

# Page 1 of 10 high-income female customers
curl -s "http://127.0.0.1:8000/customers?genre=Female&min_income=100&limit=10"

# Top 5 spenders
curl -s "http://127.0.0.1:8000/customers?sort_by=spending_score&sort_order=desc&limit=5"

# Search by id substring
curl -s "http://127.0.0.1:8000/customers?search=199"

# Create
curl -s -X POST http://127.0.0.1:8000/customers \
  -H "content-type: application/json" \
  -d '{"genre":"Female","age":28,"annual_income_k":75,"spending_score":88}'

# Partial update
curl -s -X PATCH http://127.0.0.1:8000/customers/201 \
  -H "content-type: application/json" \
  -d '{"spending_score":99}'

# Delete
curl -s -X DELETE http://127.0.0.1:8000/customers/201 -i
```

## Validation and error handling

- Pydantic enforces field types and ranges (`spending_score` in 1..100, etc.).
  Violations return `422 Unprocessable Entity` with a structured error body.
- Inconsistent min/max query ranges return `400 Bad Request`.
- Reads/updates/deletes against unknown IDs return `404 Not Found`.
- Creates with a colliding `customer_id` return `409 Conflict`.

## Known limitations and future improvements

- **SQLite only.** The connection layer assumes a single-process local DB. For
  multi-instance deployments, swap in Postgres via `SHOPPING_DATABASE_URL`.
- **No auth.** All endpoints are public — fine for local exploration, not for
  production. Add an API key / OAuth dependency before exposing publicly.
- **Tiny dataset.** 200 rows fit easily in memory; the current `LIKE`-based
  search would not scale to millions of rows. Move to full-text search (FTS5
  in SQLite, or `tsvector` in Postgres) for larger corpora.
- **No clustering or analytics endpoints.** The dataset is commonly used for
  customer-segmentation experiments (e.g. k-means on income vs. spending
  score); exposing precomputed segments would be a natural next step.
- **No migrations.** Schema is managed with `create_all`. For evolving schemas
  switch to Alembic.
- **Importer is idempotent but destructive** — it truncates `customers` before
  re-importing. An "upsert" mode would be useful for incremental data.
