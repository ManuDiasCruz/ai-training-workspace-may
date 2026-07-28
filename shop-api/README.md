# 🛒 Shop API — REST API over the shopping dataset

A small production-style backend: a local SQLite database built from the
`Shopping_data.csv` shopping dataset, and a read-only **FastAPI** REST service
over it with pagination, filtering, search, aggregates, input validation and
consistent error handling.

Branch: **`723-oeh-shop-api`** · Project directory: **`shop-api/`**

> This directory is self-contained. The rest of the repository is an unrelated
> static game project and is untouched by this branch.

---

## Table of contents

- [The dataset](#the-dataset)
- [Database design](#database-design)
- [Setup](#setup)
- [Running it](#running-it)
- [API reference](#api-reference)
- [Usage examples](#usage-examples)
- [Error handling](#error-handling)
- [Tests](#tests)
- [Project layout](#project-layout)
- [Known limitations & future improvements](#known-limitations--future-improvements)

---

## The dataset

Source: `Shopping_data.csv`, exported from Google Drive and committed to
`data/Shopping_data.csv` (4,286 bytes, sha256 `293887b3a8de…`). It is the
well-known *Mall Customers* dataset.

**200 rows, 5 columns, no missing values.** Profiled before designing the schema:

| Source column            | Type    | Observed range / values      |
| ------------------------ | ------- | ---------------------------- |
| `CustomerID`             | text    | `0001`–`0200`, unique, zero-padded to 4 digits |
| `Genre`                  | text    | `Male` (88), `Female` (112)  |
| `Age`                    | integer | 18 – 70 (mean 38.85)         |
| `Annual Income (k$)`     | integer | 15 – 137 (mean 60.56)        |
| `Spending Score (1-100)` | integer | 1 – 99 (mean 50.20)          |

Two observations drove the design:

- **`Genre` actually holds gender**, not a music/film genre. The column is
  mapped to `gender` in the database; the original header is recorded in
  `app/schema.sql` so the mapping is traceable.
- **`CustomerID` is a zero-padded string**, not a bare integer. `0001` and `1`
  are the same customer, but only `0001` is what the source file says — so both
  representations are preserved (see below).

The vendored CSV is pinned with `data/*.csv -text` in `.gitattributes`. Without
it, `core.autocrlf` would rewrite the file's CRLF line endings on checkout and
the dataset would no longer be byte-identical to the Drive export.

---

## Database design

**Engine:** SQLite (`shop.db`) — a single file, no server to run, and part of
the Python standard library, which suits a 200-row read-mostly dataset. The
schema lives in [`app/schema.sql`](app/schema.sql).

### `customers` — one row per record

| Column            | Type    | Constraints                              |
| ----------------- | ------- | ---------------------------------------- |
| `id`              | INTEGER | `PRIMARY KEY` — numeric id, 1–200        |
| `customer_id`     | TEXT    | `NOT NULL UNIQUE` — canonical `'0001'`   |
| `gender`          | TEXT    | `NOT NULL CHECK (gender IN ('Male','Female'))` |
| `age`             | INTEGER | `NOT NULL CHECK (age BETWEEN 0 AND 120)` |
| `annual_income_k` | INTEGER | `NOT NULL CHECK (>= 0)` — thousands of USD |
| `spending_score`  | INTEGER | `NOT NULL CHECK (BETWEEN 1 AND 100)`     |

**Why one table.** The dataset is a single flat observation table: every column
is a scalar attribute of exactly one customer, with no repeating groups and no
transitive dependencies. It is therefore already in 3NF. Splitting the
two-value `gender` domain into a lookup table would add a join to every query
without eliminating any redundancy, so the domain is enforced with a `CHECK`
constraint instead — the constraint does the same work at no query cost.

**Why two id columns.** `id` is an `INTEGER PRIMARY KEY`, which in SQLite
aliases the internal `rowid` — so it costs no extra storage and gives the
fastest possible lookups and a natural sort order. `customer_id` keeps the
source's exact zero-padded text, so responses can round-trip the CSV's own
representation. The API accepts either form on lookup and always returns the
canonical one.

**Indexes.** `gender`, `age`, `annual_income_k`, `spending_score` — one per
exposed filter and sort key, covering both the equality filter and the three
range filters.

### `import_metadata` — provenance

Single-row table (`CHECK (id = 1)`) recording the source filename, its sha256,
the row count and the import timestamp. It serves two purposes: `/health`
reports what is actually loaded, and the importer compares checksums to skip an
unchanged reimport.

### `customers_enriched` — derived read model

A view that adds a coarse `segment` from the income/spending quadrant. The API
reads this view, so the rule is defined once in SQL and is directly filterable.

| Segment    | Rule                              | Rows | Reading                    |
| ---------- | --------------------------------- | ---: | -------------------------- |
| `careless` | income ≤ 40 **and** score ≥ 60    |   23 | Low income, high spend     |
| `frugal`   | income ≤ 40 **and** score ≤ 40    |   23 | Low income, low spend      |
| `target`   | income ≥ 70 **and** score ≥ 60    |   38 | High income, high spend    |
| `cautious` | income ≥ 70 **and** score ≤ 40    |   38 | High income, low spend     |
| `standard` | everything else (the middle band) |   78 | Mid income and/or mid spend |

> ⚠️ These thresholds are a **documented heuristic, not a clustering result.**
> This dataset is conventionally analysed with k-means (k=5); the fixed cuts
> above approximate those groups well enough to be a useful filter, and they
> partition the data symmetrically (23/23 and 38/38), but they are a business
> rule chosen here — not a statistical finding. See
> [future improvements](#known-limitations--future-improvements).

---

## Setup

Requires **Python 3.10+** (developed on 3.12).

```bash
cd shop-api

# 1. Install dependencies (a virtualenv is recommended)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Build the database from the CSV
python scripts/import_data.py
```

Expected output:

```text
Shopping_data.csv imported: 200 rows -> .../shop-api/shop.db
  sha256: 293887b3a8de822afa42629d01c2679006adcc8269890b19eba1ff8ab4a49075
```

The importer is **idempotent** — a second run detects the unchanged checksum
and skips the work (`--force` reimports anyway). It validates the entire CSV
before writing and inserts in one transaction, so a malformed row fails cleanly
instead of leaving a half-loaded table.

`shop.db` is generated and git-ignored; rebuild it any time with the command
above.

### Optional configuration

| Variable       | Default                   | Purpose                     |
| -------------- | ------------------------- | --------------------------- |
| `SHOP_API_DB`  | `shop-api/shop.db`        | Database file location      |
| `SHOP_API_CSV` | `shop-api/data/Shopping_data.csv` | Source CSV location |

---

## Running it

```bash
# from shop-api/
python -m uvicorn app.main:app --reload --port 8000
```

| URL                              | What                          |
| -------------------------------- | ----------------------------- |
| http://127.0.0.1:8000/docs       | Interactive Swagger UI        |
| http://127.0.0.1:8000/redoc      | ReDoc reference              |
| http://127.0.0.1:8000/openapi.json | OpenAPI 3 schema            |
| http://127.0.0.1:8000/health     | Health + loaded-dataset info  |

---

## API reference

Base path: **`/api/v1`**

| Method | Path                       | Description                                  |
| ------ | -------------------------- | -------------------------------------------- |
| `GET`  | `/health`                  | Liveness, record count, import provenance    |
| `GET`  | `/api/v1/customers`        | List records — paginated, filterable, searchable |
| `GET`  | `/api/v1/customers/{id}`   | One record by id (`0001` or `1`)             |
| `GET`  | `/api/v1/stats`            | Dataset-wide aggregates                      |

### `GET /api/v1/customers` parameters

| Parameter    | Type    | Default       | Notes                                        |
| ------------ | ------- | ------------- | -------------------------------------------- |
| `page`       | int     | `1`           | ≥ 1                                          |
| `page_size`  | int     | `20`          | 1 – 100                                      |
| `gender`     | enum    | —             | `Male` / `Female`, case-insensitive          |
| `segment`    | enum    | —             | `careless`, `frugal`, `target`, `cautious`, `standard` |
| `age_min` / `age_max`       | int | — | 0 – 120                          |
| `income_min` / `income_max` | int | — | in k$, ≥ 0                       |
| `score_min` / `score_max`   | int | — | 1 – 100                          |
| `q`          | string  | —             | Search across `customer_id` and `gender`     |
| `sort_by`    | enum    | `customer_id` | `customer_id`, `age`, `annual_income_k`, `spending_score` |
| `order`      | enum    | `asc`         | `asc` / `desc`                               |

Filters combine with **AND**. Unknown parameters are rejected (see
[error handling](#error-handling)).

**About `q`.** The dataset has no free-text column, so "search" is a
case-insensitive substring match over the only two textual fields —
`customer_id` and the `gender` label. LIKE wildcards in the term are escaped,
so `q=%` matches nothing rather than everything. It is genuinely useful for id
lookup (`q=019`) but it is not a text-search engine; see
[limitations](#known-limitations--future-improvements).

---

## Usage examples

All responses below are real output from a running instance.

### List with pagination

```bash
curl "http://127.0.0.1:8000/api/v1/customers?page=2&page_size=3"
```

```json
{
  "meta": {
    "page": 2, "page_size": 3, "total_items": 200,
    "total_pages": 67, "has_next": true, "has_prev": true
  },
  "data": [
    {"customer_id":"0004","gender":"Female","age":23,"annual_income_k":16,"spending_score":77,"segment":"careless"},
    {"customer_id":"0005","gender":"Female","age":31,"annual_income_k":17,"spending_score":40,"segment":"frugal"},
    {"customer_id":"0006","gender":"Female","age":22,"annual_income_k":17,"spending_score":76,"segment":"careless"}
  ]
}
```

### Filter — high-earning women

```bash
curl "http://127.0.0.1:8000/api/v1/customers?gender=female&income_min=100&page_size=2"
```

```json
{
  "meta": {"page":1,"page_size":2,"total_items":9,"total_pages":5,"has_next":true,"has_prev":false},
  "data": [
    {"customer_id":"0187","gender":"Female","age":54,"annual_income_k":101,"spending_score":24,"segment":"cautious"},
    {"customer_id":"0189","gender":"Female","age":41,"annual_income_k":103,"spending_score":17,"segment":"cautious"}
  ]
}
```

### Filter by segment, sorted

```bash
curl "http://127.0.0.1:8000/api/v1/customers?segment=target&sort_by=spending_score&order=desc&page_size=2"
```

### Search

```bash
curl "http://127.0.0.1:8000/api/v1/customers?q=0199"
```

```json
{
  "meta": {"page":1,"page_size":20,"total_items":1,"total_pages":1,"has_next":false,"has_prev":false},
  "data": [
    {"customer_id":"0199","gender":"Male","age":32,"annual_income_k":137,"spending_score":18,"segment":"cautious"}
  ]
}
```

### One record — `0042` and `42` both work

```bash
curl "http://127.0.0.1:8000/api/v1/customers/0042"
```

```json
{"customer_id":"0042","gender":"Male","age":24,"annual_income_k":38,"spending_score":92,"segment":"careless"}
```

### Aggregate statistics

```bash
curl "http://127.0.0.1:8000/api/v1/stats"
```

```json
{
  "total_customers": 200,
  "age":             {"min":18,"max":70,"avg":38.85},
  "annual_income_k": {"min":15,"max":137,"avg":60.56},
  "spending_score":  {"min":1,"max":99,"avg":50.2},
  "by_gender": [
    {"gender":"Female","count":112,"avg_age":38.1,"avg_annual_income_k":59.25,"avg_spending_score":51.53},
    {"gender":"Male","count":88,"avg_age":39.81,"avg_annual_income_k":62.23,"avg_spending_score":48.51}
  ],
  "by_segment": [
    {"segment":"standard","count":78,"avg_annual_income_k":55.0,"avg_spending_score":50.41},
    {"segment":"cautious","count":38,"avg_annual_income_k":87.0,"avg_spending_score":18.63},
    {"segment":"target","count":38,"avg_annual_income_k":87.0,"avg_spending_score":81.89},
    {"segment":"careless","count":23,"avg_annual_income_k":26.3,"avg_spending_score":78.57},
    {"segment":"frugal","count":23,"avg_annual_income_k":26.3,"avg_spending_score":20.91}
  ]
}
```

### Health

```bash
curl "http://127.0.0.1:8000/health"
```

```json
{
  "status": "ok",
  "database": ".../shop-api/shop.db",
  "record_count": 200,
  "source_file": "Shopping_data.csv",
  "imported_at": "2026-07-28T14:14:52+00:00"
}
```

---

## Error handling

Every error — validation, not-found, unavailable — uses one envelope, so a
client can branch on `error.code` instead of parsing prose.

```json
{"error": {"code": "…", "message": "…", "details": [{"field": "…", "message": "…"}]}}
```

| Status | `code`                | When                                              |
| ------ | --------------------- | ------------------------------------------------- |
| `404`  | `not_found`           | No customer with that id                          |
| `422`  | `validation_error`    | Bad, out-of-range, or unknown parameter           |
| `503`  | `service_unavailable` | Database not imported yet                         |
| `500`  | `internal_error`      | Unexpected failure                                |

**Out-of-range value** — `?page_size=500`:

```json
{"error":{"code":"validation_error","message":"One or more request parameters are invalid.",
 "details":[{"field":"page_size","message":"Input should be less than or equal to 100"}]}}
```

**Unknown parameter** — `?genderr=Male`. A typo'd filter fails loudly rather
than being silently ignored, which would otherwise return unfiltered data that
looks correct:

```json
{"error":{"code":"validation_error","message":"One or more request parameters are invalid.",
 "details":[{"field":"genderr","message":"Extra inputs are not permitted"}]}}
```

**Inverted range** — `?age_min=60&age_max=20`. Caught by a cross-field
validator; without it the request would return a puzzling empty page:

```json
{"error":{"code":"validation_error","message":"One or more request parameters are invalid.",
 "details":[{"message":"age_min (60) must be less than or equal to age_max (20)"}]}}
```

**Database not imported** — 503 rather than 500, because the service is fine and
the fix is known:

```json
{"error":{"code":"service_unavailable",
 "message":"Database not found at …/shop.db. Run 'python scripts/import_data.py' to create it."}}
```

### Injection safety

Sort keys resolve through an allow-list and every value is a bound parameter, so
no user input reaches SQL as text. The API's connection is opened in SQLite's
**read-only mode**, so even a bug cannot mutate the imported dataset. Both
properties are covered by tests.

---

## Tests

```bash
cd shop-api
python -m pytest          # 45 passed
```

Each run rebuilds the database from the committed CSV through the real importer,
so the ingest path is exercised on every run rather than mocked. Coverage spans
listing, pagination, filtering, search, sorting, validation, error envelopes and
aggregates. A few cases worth calling out:

- **`test_pagination_walks_every_record_exactly_once`** pages through all 200
  records and asserts no duplicates and no gaps — this catches off-by-one offset
  errors that per-page assertions miss.
- **`test_search_treats_like_wildcards_literally`** pins `q=%` to zero results.
- **`test_sql_injection_attempt_does_not_execute`** sends a `DROP TABLE` payload
  and asserts the table is still intact afterwards.
- **`test_stats_match_the_dataset`** asserts the aggregates against values
  computed independently from the CSV.
- **`test_missing_database_returns_503_with_guidance`** covers the un-imported
  startup path.

---

## Project layout

```text
shop-api/
├── app/
│   ├── main.py            # FastAPI app, error handlers, /health
│   ├── config.py          # paths and limits (env-overridable)
│   ├── db.py              # connections (read-only by default)
│   ├── models.py          # Pydantic request validation + response shapes
│   ├── repository.py      # all SQL lives here
│   ├── schema.sql         # DDL: tables, indexes, view
│   └── routers/
│       └── customers.py   # endpoint definitions
├── scripts/
│   └── import_data.py     # CSV -> SQLite, idempotent and transactional
├── tests/
│   ├── conftest.py        # builds a scratch DB via the real importer
│   └── test_api.py        # 45 tests
├── data/
│   └── Shopping_data.csv  # source dataset (byte-identical to Drive export)
├── requirements.txt
└── pytest.ini
```

The layers are separated so each has one job: `routers` handles HTTP,
`repository` owns SQL, `models` owns validation. Swapping SQLite for Postgres
would touch `db.py` and `repository.py` only.

---

## Known limitations & future improvements

**Limitations of the current implementation**

1. **Read-only API.** There are no `POST`/`PATCH`/`DELETE` endpoints. The
   dataset is a fixed 200-row export, so writes had no clear meaning here — but
   it does mean the API cannot be used to correct or extend the data.
2. **Search is a substring match, not text search.** The dataset has no
   free-text column, so `q` can only target `customer_id` and `gender`. It uses
   `LIKE '%term%'`, which cannot use an index — irrelevant at 200 rows, but it
   would degrade linearly on a larger table.
3. **Segment thresholds are hardcoded and heuristic.** The income/spending cuts
   in the `customers_enriched` view are a business rule chosen for this dataset,
   not a clustering result, and they are baked into the schema rather than
   configurable.
4. **Offset pagination.** `LIMIT/OFFSET` makes deep pages progressively more
   expensive and can skip or repeat rows if the underlying data changes
   mid-scan. Fine for a static 200-row dataset; not for a live table.
5. **No auth, rate limiting, or CORS policy.** The service is unauthenticated
   and intended for local use. It should not be exposed publicly as-is.
6. **Single-file SQLite, no migrations.** Schema changes currently mean
   re-running the importer; there is no versioned migration history.
7. **No structured logging or metrics.** Only uvicorn's default access log; no
   request ids, no latency histograms.
8. **`gender` is constrained to the dataset's two values.** That faithfully
   reflects the source data, but the `CHECK` constraint would need revisiting
   before this schema were used for real customer records.

**Improvements worth doing next** — each of these is filed as a GitHub issue
against this branch:

- Write endpoints (`POST`/`PATCH`/`DELETE`) with optimistic concurrency.
- Replace the heuristic segments with real k-means clustering (k=5) computed at
  import time and stored, keeping the API contract identical.
- Cursor-based (keyset) pagination alongside the current offset mode.
- SQLite **FTS5** full-text search, so `q` is index-backed and extensible.
- API-key auth plus per-key rate limiting.
- Dockerfile and CI workflow running the test suite on every push.
- Structured JSON logging with request ids, and a `/metrics` endpoint.
- Versioned migrations (Alembic or plain SQL) instead of import-time DDL.
