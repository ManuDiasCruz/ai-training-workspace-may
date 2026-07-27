# Shopping Customer API

A small, locally runnable, read-only REST API for a shopping customer dataset.
The source CSV is validated and imported into SQLite, and FastAPI exposes
stable customer listing, pagination, exact/range filters, partial search, and
individual lookup. This project is intentionally contained in `shopping-api/`
so it can coexist with the original repository's browser game.

## Dataset

The supplied [Google Drive source](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing)
is `Shopping_data.csv`. A reproducible snapshot is committed at
`data/Shopping_data.csv`. It has 200 data rows and these exact headers:

| Source header | Meaning | Observed values |
| --- | --- | --- |
| `CustomerID` | Zero-padded source identifier | `0001`–`0200` |
| `Genre` | Source demographic category | 112 `Female`, 88 `Male` |
| `Age` | Age in years | 18–70 |
| `Annual Income (k$)` | Annual income in thousands of dollars | 15–137 |
| `Spending Score (1-100)` | Dataset score | 1–99 in this snapshot |

The API calls the `Genre` column `gender` because its observed values are
`Female` and `Male`. That is a naming normalization, not an assertion about
how the original dataset was collected. The source column and values remain
unchanged in the CSV.

## Database design

SQLite is appropriate for a compact, single-machine, read-mostly snapshot. The
generated file defaults to `data/shopping.db` and is ignored by Git; rebuild it
from the committed CSV. The single `customers` table is deliberately simple:

| Column | SQLite type | Constraints / purpose |
| --- | --- | --- |
| `customer_id` | `TEXT` | Primary key; exactly four digits, preserving leading zeroes |
| `gender` | `TEXT` | Required, nonblank source `Genre` value |
| `age` | `INTEGER` | Required; `0–120` |
| `annual_income_k` | `INTEGER` | Required; nonnegative; units are k$ |
| `spending_score` | `INTEGER` | Required; `1–100` |

Indexes support the exact gender and numeric range filters (`gender`, `age`,
`annual_income_k`, and `spending_score`). The primary key supports deterministic
ordering and detail lookup. The importer rejects unexpected headers, missing or
extra columns, duplicate IDs, invalid integers, out-of-range values, and empty
input. It validates the complete source before opening a write transaction, then
deletes and inserts the snapshot atomically. A failed row validation does not
partially replace an existing snapshot.

## Setup

Use Python 3.10 or newer. Run all commands below from the `shopping-api/`
directory:

```bash
cd shopping-api
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the runtime and test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

For a runtime-only installation, use `requirements.txt` instead.

## Import and run

Create or replace the local SQLite snapshot:

```bash
python -m app.import_data
# Imported 200 customers into .../shopping-api/data/shopping.db
```

Optional paths can be supplied explicitly:

```bash
python -m app.import_data --csv /path/to/Shopping_data.csv --db /path/to/shopping.db
```

When using a nondefault database, point the server at the same path:

```bash
# macOS / Linux
export SHOPPING_DB_PATH=/path/to/shopping.db

# Windows PowerShell
$env:SHOPPING_DB_PATH = 'C:\path\to\shopping.db'
```

Start the local development server:

```bash
python -m uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is at
`/docs` and the schema is at `/openapi.json`. If the database has not been
imported, database-backed endpoints return an actionable `503` response rather
than silently creating an empty database.

## API usage

| Method and path | Purpose |
| --- | --- |
| `GET /health` | Database-backed health check and imported record count |
| `GET /customers` | Paginated list with optional filters and search |
| `GET /customers/{customer_id}` | One customer by four-digit ID |

`GET /customers` accepts these combinable query parameters:

| Parameter | Contract |
| --- | --- |
| `page` | One-based, default `1`, maximum `1000000` |
| `page_size` | Default `20`, range `1–100` |
| `gender` | `male` or `female`; exact match against the source value, case-insensitive in SQL |
| `min_age`, `max_age` | Inclusive age bounds, each `0–120` |
| `min_income`, `max_income` | Inclusive nonnegative income bounds in k$ |
| `min_score`, `max_score` | Inclusive score bounds, each `1–100` |
| `q` | 1–50-character partial customer ID or gender search; whitespace-only is rejected |

Results are always ordered by `customer_id`. Search is case-insensitive for the
ASCII values in this dataset, and SQL wildcard characters in `q` are treated as
literal text. Filters are combined with `AND`; `q` matches either ID or gender.

```bash
curl 'http://127.0.0.1:8000/health'
curl 'http://127.0.0.1:8000/customers?page=2&page_size=3'
curl 'http://127.0.0.1:8000/customers?gender=female&min_income=100&min_score=80&q=female'
curl 'http://127.0.0.1:8000/customers/0001'
```

In Windows PowerShell, use `curl.exe` if `curl` resolves to the PowerShell web
request alias. A listing response has explicit navigation metadata:

```json
{
  "items": [
    {
      "customer_id": "0004",
      "gender": "Female",
      "age": 23,
      "annual_income_k": 16,
      "spending_score": 77
    }
  ],
  "total": 200,
  "page": 2,
  "page_size": 3,
  "total_pages": 67,
  "next_page": 3,
  "previous_page": 1
}
```

An unknown well-formed ID returns `404`. Invalid path/query types, bounds,
reversed ranges, or whitespace search return `422`. A missing or unusable
database returns `503`. SQL parameters are bound rather than interpolating user
values.

## Tests

```bash
python -m pytest -q
```

The API tests import the committed CSV into a temporary database, so they do not
depend on or mutate `data/shopping.db`. They cover health, pagination, combined
filter/search behavior, detail and not-found responses, validation, and the
missing-database error.

## Known limitations and future improvements

- This is a read-only snapshot API. There are no create/update/delete routes,
  authentication, authorization, rate limiting, or audit logging. It should not
  be exposed publicly as-is.
- SQLite is a practical local store, but there is no migration framework,
  connection pool, backup policy, or multi-instance deployment strategy.
- Search is a simple substring match over ID and gender. It is not full-text,
  ranked, multilingual, or designed for a large dataset.
- The importer replaces a full snapshot and has no incremental ingestion,
  provenance table, duplicate-file detection, or row-level rejection report.
- Direct dependencies are pinned, but transitive dependencies are not locked.
  CI, dependency auditing, a lockfile, linting, type checking, and a broader
  test matrix would make the project more reproducible.
- The source has only two observed `Genre` values. The API filter enum reflects
  this snapshot; future source categories would require an intentional contract
  update. The demographic data should be handled under appropriate privacy and
  governance policies before any real deployment.
