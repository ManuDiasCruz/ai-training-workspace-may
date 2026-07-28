# Shop API

A small, production-shaped REST API over the mall shopping dataset
(`Shopping_data.csv`, 200 customers) sourced from Google Drive.

The dataset is imported into a local SQLite database and exposed over HTTP with
pagination, filtering, free-text search, sorting and aggregate statistics.
Built with **FastAPI + Pydantic v2** on **SQLite** (Python standard library —
no ORM, no external database server).

> Branch: `723-oh-shop-api` · everything lives under `shop-api/` so the
> repository's existing static site on `main` is untouched.

---

## Dataset

Downloaded from [Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view)
and vendored at `data/Shopping_data.csv` (4,286 bytes,
sha256 `293887b3a8de822afa42629d01c2679006adcc8269890b19eba1ff8ab4a49075`).

| Source column            | Type | Range        | Notes                                     |
| ------------------------ | ---- | ------------ | ----------------------------------------- |
| `CustomerID`             | text | `0001`–`0200`| Zero-padded, unique                       |
| `Genre`                  | text | Female / Male| 112 female, 88 male                       |
| `Age`                    | int  | 18–70        |                                           |
| `Annual Income (k$)`     | int  | 15–137       | Thousands of dollars                      |
| `Spending Score (1-100)` | int  | 1–99         | Mall-assigned score                       |

Profiling result: **200 rows, no missing values, no duplicates, no malformed
numbers.** The importer still validates every row, because a clean file today
is not a guarantee about the next drop of the file.

---

## Database design

One table, because the source is one flat entity — inventing `orders` or
`products` tables would mean inventing data that does not exist.

### `customers`

| Column            | Type    | Constraint                                |
| ----------------- | ------- | ----------------------------------------- |
| `id`              | INTEGER | `PRIMARY KEY` — numeric form of `CustomerID` (`"0007"` → `7`) |
| `customer_ref`    | TEXT    | `NOT NULL UNIQUE` — original padded id, kept for traceability |
| `gender`          | TEXT    | `CHECK (gender IN ('Female','Male'))`     |
| `age`             | INTEGER | `CHECK (age BETWEEN 0 AND 120)`           |
| `annual_income_k` | INTEGER | `CHECK (annual_income_k >= 0)`            |
| `spending_score`  | INTEGER | `CHECK (spending_score BETWEEN 1 AND 100)`|
| `age_bracket`     | TEXT    | `GENERATED ALWAYS AS (…) STORED`          |
| `income_band`     | TEXT    | `GENERATED ALWAYS AS (…) STORED`          |
| `spending_tier`   | TEXT    | `GENERATED ALWAYS AS (…) STORED`          |

The three segment labels are **generated columns computed by SQLite**, not
values written by the application. They therefore cannot drift out of sync with
the raw numbers they derive from, and because they are `STORED` they are also
indexed and filterable at no query cost:

| Label           | Rule                                              |
| --------------- | ------------------------------------------------- |
| `age_bracket`   | `under-25`, `25-34`, `35-44`, `45-54`, `55-plus`  |
| `income_band`   | `low` < 40k · `medium` 40–79k · `high` ≥ 80k      |
| `spending_tier` | `low` < 35 · `medium` 35–64 · `high` ≥ 65         |

Indexes cover `gender`, `age`, `annual_income_k`, `spending_score` and all
three label columns, so every documented filter is index-backed.

### `import_runs`

Provenance, one row per import: `source_file`, `source_sha256`, `rows_read`,
`rows_imported`, `rows_rejected`, `imported_at`. Any database file can be traced
back to the exact CSV bytes it was built from, and `/health` surfaces the most
recent run.

The full DDL is in [`app/schema.sql`](app/schema.sql).

---

## Setup

Requires **Python 3.10+** (developed on 3.12).

```bash
cd shop-api

python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt        # runtime
pip install -r requirements-dev.txt    # runtime + pytest, httpx
```

## Execution

**1. Import the dataset** (creates `data/shopping.db`):

```bash
python -m app.importer
```

```text
source     : .../shop-api/data/Shopping_data.csv
database   : .../shop-api/data/shopping.db
rows read  : 200
imported   : 200
rejected   : 0
customers in database: 200
```

The import is **idempotent** — it upserts by customer id, so re-running it
leaves 200 rows. Useful flags: `--csv PATH`, `--db PATH`, `--reset` (clear
existing rows first).

**2. Start the API:**

```bash
python -m uvicorn app.main:app --reload --port 8000
```

- Interactive docs: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

**3. Run the tests:**

```bash
python -m pytest
```

```text
55 passed
```

The suite builds its own throwaway database from the real CSV and never touches
`data/shopping.db`.

### Configuration

| Variable            | Default                     | Purpose                |
| ------------------- | --------------------------- | ---------------------- |
| `SHOP_API_DB_PATH`  | `data/shopping.db`          | SQLite file location   |
| `SHOP_API_CSV_PATH` | `data/Shopping_data.csv`    | Default import source  |

---

## API

Base path: `/api/v1`

| Method | Path                        | Purpose                                          |
| ------ | --------------------------- | ------------------------------------------------ |
| GET    | `/`                         | Service metadata and endpoint index              |
| GET    | `/health`                   | Liveness plus data readiness and last import     |
| GET    | `/api/v1/customers`         | List with pagination, filters, search, sorting   |
| GET    | `/api/v1/customers/{id}`    | Single customer                                  |
| GET    | `/api/v1/stats`             | Aggregates and segment breakdowns                |

### `GET /api/v1/customers` parameters

| Parameter                                 | Type   | Default | Validation                       |
| ----------------------------------------- | ------ | ------- | -------------------------------- |
| `page`                                    | int    | `1`     | ≥ 1                              |
| `page_size`                               | int    | `20`    | 1–100                            |
| `gender`                                  | enum   | —       | `Female` \| `Male`               |
| `min_age` / `max_age`                     | int    | —       | 0–120, `min ≤ max`               |
| `min_income` / `max_income`               | int    | —       | ≥ 0, `min ≤ max`                 |
| `min_spending_score` / `max_spending_score` | int  | —       | 1–100, `min ≤ max`               |
| `age_bracket`                             | enum   | —       | `under-25` … `55-plus`           |
| `income_band`                             | enum   | —       | `low` \| `medium` \| `high`      |
| `spending_tier`                           | enum   | —       | `low` \| `medium` \| `high`      |
| `q`                                       | string | —       | 1–64 chars, substring search     |
| `sort_by`                                 | enum   | `id`    | `id`, `age`, `annual_income_k`, `spending_score`, `gender` |
| `order`                                   | enum   | `asc`   | `asc` \| `desc`                  |

Filters combine with `AND`. `q` searches `customer_ref`, `gender`,
`age_bracket`, `income_band` and `spending_tier`.

### Usage examples

**Paginated listing**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?page=1&page_size=2"
```

```json
{
  "data": [
    {
      "id": 1,
      "customer_ref": "0001",
      "gender": "Male",
      "age": 19,
      "annual_income_k": 15,
      "spending_score": 39,
      "age_bracket": "under-25",
      "income_band": "low",
      "spending_tier": "medium"
    },
    {
      "id": 2,
      "customer_ref": "0002",
      "gender": "Male",
      "age": 21,
      "annual_income_k": 15,
      "spending_score": 81,
      "age_bracket": "under-25",
      "income_band": "low",
      "spending_tier": "high"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 2,
    "total_items": 200,
    "total_pages": 100,
    "has_next": true,
    "has_prev": false
  },
  "filters_applied": {}
}
```

**Filtering — high-income women who spend heavily** (9 matches)

```bash
curl "http://127.0.0.1:8000/api/v1/customers?gender=Female&income_band=high&min_spending_score=70"
```

**Filtering — a numeric range**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?min_age=30&max_age=40&max_income=60"
```

**Search — by partial customer reference**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?q=0042"
```

**Search — by segment label**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?q=under-25&page_size=50"
```

**Sorting — biggest spenders first**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?sort_by=spending_score&order=desc&page_size=5"
```

**Single customer** — `0007` and `7` both resolve

```bash
curl "http://127.0.0.1:8000/api/v1/customers/0007"
```

```json
{
  "id": 7,
  "customer_ref": "0007",
  "gender": "Female",
  "age": 35,
  "annual_income_k": 18,
  "spending_score": 6,
  "age_bracket": "35-44",
  "income_band": "low",
  "spending_tier": "low"
}
```

**Statistics**

```bash
curl "http://127.0.0.1:8000/api/v1/stats"
```

```json
{
  "total_customers": 200,
  "age": { "min": 18, "max": 70, "avg": 38.85 },
  "annual_income_k": { "min": 15, "max": 137, "avg": 60.56 },
  "spending_score": { "min": 1, "max": 99, "avg": 50.2 },
  "by_gender": [
    { "value": "Female", "count": 112, "avg_spending_score": 51.53 },
    { "value": "Male", "count": 88, "avg_spending_score": 48.51 }
  ],
  "by_income_band": [
    { "value": "high", "count": 38, "avg_spending_score": 50.55 },
    { "value": "low", "count": 46, "avg_spending_score": 49.74 },
    { "value": "medium", "count": 116, "avg_spending_score": 50.27 }
  ],
  "by_spending_tier": [
    { "value": "high", "count": 59, "avg_spending_score": 81.78 },
    { "value": "low", "count": 50, "avg_spending_score": 15.68 },
    { "value": "medium", "count": 91, "avg_spending_score": 48.69 }
  ],
  "by_age_bracket": [
    { "value": "25-34", "count": 54, "avg_spending_score": 63.17 },
    { "value": "35-44", "count": 42, "avg_spending_score": 49.43 },
    { "value": "45-54", "count": 39, "avg_spending_score": 36.23 },
    { "value": "55-plus", "count": 30, "avg_spending_score": 39.03 },
    { "value": "under-25", "count": 35, "avg_spending_score": 56.26 }
  ]
}
```

### Validation and errors

Every error uses one envelope, so clients parse failures the same way everywhere:

```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more query parameters are invalid.",
    "details": [
      { "field": "gender", "message": "Input should be 'Female' or 'Male'", "type": "enum" }
    ]
  }
}
```

| Status | `code`                     | Cause                                              |
| ------ | -------------------------- | -------------------------------------------------- |
| 400    | `invalid_range`            | `min_age=50&max_age=20` and similar contradictions |
| 404    | `customer_not_found`       | Unknown customer id                                |
| 404    | `http_error`               | Unknown route                                      |
| 422    | `validation_error`         | Bad type, out-of-bounds number, unknown enum value |
| 500    | `database_error`           | Unexpected SQLite failure                          |
| 503    | `database_not_initialised` | Importer has not been run yet                      |

Notes on the safety properties:

- All filter and search values are passed as **bound parameters**. `sort_by`
  and `order` are the only inputs that reach SQL text, and both are closed
  enums — `?sort_by=id;+DROP+TABLE+customers` is rejected with 422 (there is a
  test asserting the table survives).
- `%` and `_` in `q` are escaped, so searching for `%` finds literal `%`
  (0 rows) instead of matching everything.
- A missing database returns a 503 telling you to run the importer, rather than
  leaking a raw `sqlite3` error.

---

## Project layout

```text
shop-api/
├── app/
│   ├── config.py      # env-driven settings
│   ├── db.py          # connections, schema bootstrap, readiness check
│   ├── importer.py    # CSV → SQLite (python -m app.importer)
│   ├── main.py        # FastAPI app, routes, error handlers
│   ├── models.py      # Pydantic models and enums
│   ├── queries.py     # parameterised SQL for list/search/stats
│   └── schema.sql     # DDL
├── data/
│   ├── Shopping_data.csv   # source dataset (committed)
│   └── shopping.db         # generated (git-ignored)
├── tests/
│   ├── test_api.py         # HTTP behaviour
│   └── test_importer.py    # import and constraint behaviour
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

---

## Known limitations and future improvements

**Limitations**

1. **Read-only.** No `POST`/`PATCH`/`DELETE`. The dataset is a fixed analytical
   extract, so write endpoints would need an ownership story that does not
   exist yet.
2. **Search is a plain substring match.** Convenient (`q=004` matches `0042`,
   `0040`…) but it means `q=male` also matches `Female`, since "Female"
   contains "male". There is a test pinning that behaviour so it is a
   documented property, not a surprise. It also cannot rank results.
3. **Offset pagination.** `LIMIT/OFFSET` is fine for 200 rows; deep offsets
   degrade on large tables and are unstable if rows are inserted mid-scan.
4. **No authentication or rate limiting.** Intended for local use.
5. **Segment thresholds are hardcoded** in `schema.sql`. Changing a band means
   a migration, and there are no migrations — schema changes today mean
   deleting `shopping.db` and re-importing.
6. **Single-process SQLite.** No connection pooling and no WAL mode; concurrent
   writers would contend. Reads are unaffected at this scale.
7. **The dataset itself is thin.** `Genre` is binary, income is pre-rounded to
   thousands, and there is no time dimension, so no trend or cohort analysis is
   possible.
8. **Manual dataset refresh.** The CSV is vendored; a new Drive export must be
   downloaded and re-imported by hand.

**Future improvements** (each tracked as a GitHub issue)

1. Write endpoints with optimistic concurrency.
2. Ranked search via SQLite FTS5, with exact-prefix boosting for `customer_ref`.
3. Keyset (cursor) pagination alongside the current page/size interface.
4. API-key authentication plus per-key rate limiting.
5. Alembic-style migrations so segment thresholds can change without a rebuild.
6. A `/segments` endpoint exposing k-means clusters over income × spending
   score — the analysis this dataset is classically used for.
7. Response caching and `ETag`/`If-None-Match` on the aggregate endpoints.
8. CI on GitHub Actions running pytest plus `ruff` and `mypy`.
