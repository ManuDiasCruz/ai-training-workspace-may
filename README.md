# ShopAPI

A small, production-style **read-only REST API** over a shopping dataset of 200
mall customers. FastAPI serves validated HTTP endpoints with generated OpenAPI
docs; SQLite persists the records locally, so there is no database server to
install.

> **Branch:** `731-oeh-shopapi`
>
> The dataset comes from
> [Shopping_data.csv on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing).
> A verified copy is committed at [`data/Shopping_data.csv`](data/Shopping_data.csv)
> (4,286 bytes, byte-identical to the Drive original), so setup needs no Drive
> credentials and no network access once dependencies are installed.

---

## Contents

- [The dataset](#the-dataset)
- [Database design](#database-design)
- [Setup](#setup)
- [Running it](#running-it)
- [API reference](#api-reference)
- [Usage examples](#usage-examples)
- [Error handling](#error-handling)
- [Tests](#tests)
- [Project layout](#project-layout)
- [Known limitations](#known-limitations)
- [Future improvements](#future-improvements)

---

## The dataset

A flat CSV of 200 rows and 5 columns, with no missing values and no duplicate
identifiers:

| CSV column               | Example | Range in the data          |
| ------------------------ | ------- | -------------------------- |
| `CustomerID`             | `0001`  | `0001`–`0200`, contiguous  |
| `Genre`                  | `Male`  | `Male` (88), `Female` (112)|
| `Age`                    | `19`    | 18 – 70                    |
| `Annual Income (k$)`     | `15`    | 15 – 137 (thousands USD)   |
| `Spending Score (1-100)` | `39`    | 1 – 99                     |

`Genre` holds gender values despite its name; the name is kept to stay faithful
to the source.

---

## Database design

**Engine:** SQLite (file-backed, zero configuration, bundled with Python).

The source is a single flat table with no repeating groups, so it maps to one
table. Normalising `genre` into a lookup table would add a join to resolve a
two-value domain — a `CHECK` constraint expresses the same invariant for free.

### `customers`

| Column            | Type      | Constraints                              | Notes |
| ----------------- | --------- | ---------------------------------------- | ----- |
| `customer_id`     | `TEXT`    | `PRIMARY KEY`, `GLOB '[0-9][0-9][0-9][0-9]'` | Zero-padded original ID, kept verbatim |
| `genre`           | `TEXT`    | `NOT NULL`, `IN ('Male','Female')`       | Closed domain |
| `age`             | `INTEGER` | `NOT NULL`, `BETWEEN 0 AND 120`          | |
| `annual_income_k` | `INTEGER` | `NOT NULL`, `>= 0`                       | Thousands of USD; unit in the name |
| `spending_score`  | `INTEGER` | `NOT NULL`, `BETWEEN 1 AND 100`          | Higher = spends more |

Design decisions worth flagging:

- **`customer_id` is `TEXT`, not `INTEGER`.** The source IDs are zero-padded
  (`0001`), and storing them as integers would silently rewrite them to `1`.
  Because the width is fixed at four digits, lexicographic ordering is also
  numeric ordering, so `ORDER BY customer_id` needs no `CAST`.
- **`STRICT` tables.** SQLite otherwise accepts a string into an `INTEGER`
  column. `STRICT` makes the declared types actually binding. (Requires SQLite
  3.37+, bundled with Python 3.11+.)
- **`CHECK` constraints mirror the real data domains,** so the database rejects
  impossible records even if something writes to it without going through the
  importer.

Four indexes back exactly the filter and sort parameters the API exposes —
`genre`, `age`, `annual_income_k`, `spending_score`. There are no speculative
indexes.

### `import_runs`

Provenance for each load: `source_file`, `source_sha256`, `row_count`,
`imported_at` (ISO-8601 UTC). This answers "which file produced the rows I am
serving, and when?" from inside the database rather than from shell history,
and the checksum makes a silent dataset swap detectable. Surfaced through
`GET /api/v1/stats` as `last_import`.

The schema lives in [`app/schema.sql`](app/schema.sql) and is the single source
of truth — the importer and the test suite both execute that file.

### Import semantics

The CSV is a **snapshot, not a delta feed**, so an import *replaces* the
contents of `customers` inside a single transaction. Consequences:

- Running the importer twice leaves 200 rows, not 400 (idempotent).
- A failure part-way through rolls back to the previous snapshot; there is no
  partial load.
- Every row is validated before any write. **One invalid row aborts the
  import** — silently dropping records is how row counts quietly stop matching
  the source. Use `--skip-invalid` to import the rest and get a report of what
  was rejected and on which line.

---

## Setup

Requires **Python 3.11+**.

```bash
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git checkout 731-oeh-shopapi
```

Create a virtual environment and install dependencies:

**Windows (PowerShell)**

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements-dev.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt
```

> `requirements-dev.txt` includes the runtime dependencies plus `pytest` and
> `httpx`. For runtime only, use `requirements.txt`.

---

## Running it

**1. Build the database** (required once, before first start):

```bash
python -m scripts.import_dataset
```

```text
Import complete
  source        : .../data/Shopping_data.csv
  sha256        : 293887b3a8de822afa42629d01c2679006adcc8269890b19eba1ff8ab4a49075
  rows read     : 200
  rows imported : 200
  rows rejected : 0
  imported at   : 2026-08-06T15:00:49+00:00
```

This creates `data/shopping.db`, which is gitignored — it is generated output,
rebuildable from the committed CSV at any time.

Importer options:

| Flag             | Default                   | Purpose |
| ---------------- | ------------------------- | ------- |
| `--csv PATH`     | `data/Shopping_data.csv`  | Source CSV |
| `--db PATH`      | `data/shopping.db`        | Target database |
| `--skip-invalid` | off                       | Import valid rows and report the rest instead of aborting |

**2. Start the server:**

```bash
uvicorn app.main:app --reload
```

Then open:

- **http://127.0.0.1:8000/docs** — interactive Swagger UI
- **http://127.0.0.1:8000/redoc** — ReDoc
- `/` redirects to `/docs`

Paths are configurable via `SHOPAPI_CSV_PATH` and `SHOPAPI_DB_PATH`.

---

## API reference

Base path: `/api/v1`

| Method | Endpoint                        | Purpose |
| ------ | ------------------------------- | ------- |
| `GET`  | `/health`                       | Service and database readiness |
| `GET`  | `/api/v1/customers`             | List with pagination, filtering, search, sorting |
| `GET`  | `/api/v1/customers/{id}`        | Fetch one record |
| `GET`  | `/api/v1/stats`                 | Aggregate statistics and import provenance |

### `GET /api/v1/customers` — query parameters

| Parameter    | Type   | Default       | Notes |
| ------------ | ------ | ------------- | ----- |
| `page`       | int    | `1`           | 1-based; `1 ≤ page ≤ 10000` |
| `page_size`  | int    | `20`          | `1 ≤ page_size ≤ 100` |
| `genre`      | enum   | —             | `Male` or `Female` |
| `min_age`    | int    | —             | Inclusive, `0–120` |
| `max_age`    | int    | —             | Inclusive, `0–120` |
| `min_income` | int    | —             | Inclusive, `≥ 0` (k$) |
| `max_income` | int    | —             | Inclusive, `≥ 0` (k$) |
| `min_score`  | int    | —             | Inclusive, `1–100` |
| `max_score`  | int    | —             | Inclusive, `1–100` |
| `q`          | string | —             | Case-insensitive substring search |
| `sort_by`    | enum   | `customer_id` | `customer_id`, `age`, `annual_income_k`, `spending_score`, `genre` |
| `order`      | enum   | `asc`         | `asc` or `desc` |

Filters combine with **AND**. All bounds are **inclusive**.

**Search (`q`)** matches a case-insensitive substring of the dataset's only two
textual columns, `customer_id` and `genre` — so `?q=fem` matches all 112 female
customers and `?q=019` matches both `0019` and `0190`. `%` and `_` are matched
literally, not as wildcards. There are no name or free-text fields in this
dataset to search; see [Future improvements](#future-improvements).

**Sorting** always appends `customer_id` as a tiebreaker, so paging over a
non-unique key such as `age` cannot repeat or skip a record between pages.

---

## Usage examples

All responses below are real output from a running server.

**List the first two records**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?page_size=2"
```

```json
{
  "items": [
    {"customer_id": "0001", "genre": "Male", "age": 19, "annual_income_k": 15, "spending_score": 39},
    {"customer_id": "0002", "genre": "Male", "age": 21, "annual_income_k": 15, "spending_score": 81}
  ],
  "pagination": {
    "page": 1, "page_size": 2, "total_items": 200,
    "total_pages": 100, "has_next": true, "has_previous": false
  }
}
```

`total_items` counts everything matching the filters, not just the page, so a
client can size a pager before walking it.

**Filter — high earners who spend heavily**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?min_income=70&min_score=60&genre=Male"
```

**Search — case-insensitive**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?q=fEmAlE&page_size=1"
```

Returns `total_items: 112`.

**Sort — highest income first**

```bash
curl "http://127.0.0.1:8000/api/v1/customers?sort_by=annual_income_k&order=desc&page_size=3"
```

**Fetch one record** (zero padding optional — `7` and `0007` both work)

```bash
curl "http://127.0.0.1:8000/api/v1/customers/0007"
```

```json
{"customer_id": "0007", "genre": "Female", "age": 35, "annual_income_k": 18, "spending_score": 6}
```

**Dataset statistics**

```bash
curl "http://127.0.0.1:8000/api/v1/stats"
```

```json
{
  "total_customers": 200,
  "genre_breakdown": [
    {"genre": "Female", "count": 112, "share_pct": 56.0, "mean_age": 38.1,
     "mean_annual_income_k": 59.25, "mean_spending_score": 51.53},
    {"genre": "Male", "count": 88, "share_pct": 44.0, "mean_age": 39.81,
     "mean_annual_income_k": 62.23, "mean_spending_score": 48.51}
  ],
  "age": {"min": 18, "max": 70, "mean": 38.85},
  "annual_income_k": {"min": 15, "max": 137, "mean": 60.56},
  "spending_score": {"min": 1, "max": 99, "mean": 50.2},
  "spending_segments": [
    {"segment": "low",    "score_range": "1-33",   "count": 49, "mean_annual_income_k": 67.0},
    {"segment": "medium", "score_range": "34-66",  "count": 94, "mean_annual_income_k": 53.86},
    {"segment": "high",   "score_range": "67-100", "count": 57, "mean_annual_income_k": 66.07}
  ],
  "last_import": {
    "source_file": ".../data/Shopping_data.csv",
    "source_sha256": "293887b3a8de822afa42629d01c2679006adcc8269890b19eba1ff8ab4a49075",
    "row_count": 200,
    "imported_at": "2026-08-06T15:00:49+00:00"
  }
}
```

`spending_segments` are derived bands over `spending_score`, not stored columns.

**Health check**

```bash
curl "http://127.0.0.1:8000/health"
```

```json
{"status": "ok", "database": "ready", "customer_count": 200, "version": "1.0.0"}
```

`/health` reports database state instead of depending on it, so it still
answers when the database is missing (`"status": "degraded"`).

---

## Error handling

Every failure uses one envelope, so a client parses a single shape:

```json
{"error": {"code": "...", "message": "...", "details": [...]}}
```

| Status | `code`                  | When |
| ------ | ----------------------- | ---- |
| `404`  | `not_found`             | No record with that identifier |
| `422`  | `validation_error`      | Bad, out-of-range, or unknown parameter |
| `500`  | `database_error`        | SQLite failure (details logged, not returned) |
| `503`  | `database_unavailable`  | Database or schema missing |

**Unknown parameters are rejected, not ignored.** `?min_agee=30` returns 422
rather than an unfiltered page that a caller would misread as filtered:

```json
{"error": {"code": "validation_error",
           "message": "One or more request parameters are invalid.",
           "details": [{"field": "min_agee", "message": "Extra inputs are not permitted"}]}}
```

**Inverted ranges are rejected** — `?min_age=50&max_age=30` is satisfiable by
nothing, so it is treated as a caller mistake rather than an empty result.

**A missing database returns an actionable 503**, not a stack trace:

```json
{"error": {"code": "database_unavailable",
           "message": "Database not found at ...data/shopping.db. Create it with: python -m scripts.import_dataset"}}
```

Raw SQLite messages are logged server-side but never returned, since they can
carry schema and filesystem detail.

---

## Tests

```bash
pytest
```

```text
59 passed
```

The suite runs against a throwaway database that the **real importer** builds
from the **real CSV** — nothing is stubbed, and your `data/shopping.db` is never
touched. Expected values are computed from the CSV independently, so the tests
compare the API against the dataset rather than against itself.

Coverage includes: pagination (walking every page yields all 200 records
exactly once), inclusive filter bounds, AND-combination of filters,
case-insensitive search, literal handling of `%` in search terms, sorting,
zero-padded and unpadded lookups, the full 404/422/503 error surface, importer
validation and rollback, and the `CHECK` constraints themselves.

---

## Project layout

```text
.
├── app/
│   ├── config.py           # paths and pagination bounds (env-overridable)
│   ├── db.py               # connection handling, schema bootstrap
│   ├── errors.py           # uniform error envelope + handlers
│   ├── main.py             # FastAPI app factory
│   ├── models.py           # Pydantic request/response schemas
│   ├── repository.py       # all SQL
│   ├── routers/
│   │   ├── customers.py    # listing and single-record endpoints
│   │   └── meta.py         # /health and /stats
│   └── schema.sql          # DDL — single source of truth
├── data/
│   ├── Shopping_data.csv   # committed source dataset
│   └── shopping.db         # generated, gitignored
├── scripts/
│   └── import_dataset.py   # validating CSV → SQLite importer
├── tests/
│   ├── conftest.py
│   ├── test_api_customers.py
│   └── test_importer.py
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

> The repository root also contains `index.html`, `css/`, `img/` and `src/` from
> the unrelated Parrot Memory Game on `main`. They are untouched by this branch.

---

## Known limitations

- **Read-only.** No create/update/delete endpoints. The dataset is a fixed
  snapshot, so write operations were out of scope.
- **Search is narrow by necessity.** The dataset has no names, emails, or
  free-text fields — `q` can only search `customer_id` and `genre`. It is a
  substring `LIKE` scan, not a full-text index, so it does not use an index and
  will not stay fast on a much larger dataset.
- **No authentication or rate limiting.** Suitable for local use; not for
  public exposure as-is.
- **Offset pagination.** `LIMIT/OFFSET` is fine at 200 rows but degrades on
  large tables, where deep pages must scan everything before them.
- **Single-process SQLite.** No connection pooling and no concurrent-writer
  story. Correct for a local read-only service, insufficient for horizontal
  scaling.
- **Segment boundaries are hardcoded** (`low` 1–33, `medium` 34–66, `high`
  67–100). They are an even split, not a data-driven clustering.
- **`mean` only.** `/stats` reports min/max/mean but no median or percentiles.
- **The importer loads the whole CSV into memory.** Fine for 200 rows; it would
  need chunking for a file that does not fit in RAM.
- **CI is not configured.** Tests run locally but nothing enforces them on push.

## Future improvements

Each of these is filed as a GitHub issue against this branch:

1. **Full-text search** via SQLite FTS5, once the dataset has text fields worth
   indexing.
2. **Cursor-based (keyset) pagination** alongside offset paging, for stable and
   constant-cost deep pages.
3. **Write endpoints** (`POST`/`PATCH`/`DELETE`) with optimistic concurrency.
4. **Authentication and rate limiting** before any non-local deployment.
5. **CI workflow** running `pytest` and a linter on every push and PR.
6. **Richer statistics** — median, percentiles, and data-driven segmentation
   (e.g. k-means over income and spending score, which is the analysis this
   dataset is conventionally used for).
7. **Containerisation** with a `Dockerfile` and `docker-compose.yml`.
8. **Automated dataset refresh** that pulls from Drive and reports a checksum
   diff against `import_runs` before replacing the snapshot.
