# Shopping Customer Dataset API

A small, production-style Python REST API for the 200-row
[shopping customer dataset in Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing).
The branch `prpl-ehi-shopping-api-dataset` validates the CSV, persists a
reproducible snapshot in SQLite, and exposes read-only customer listing,
pagination, filters, search, record lookup, dataset metadata, and health
operations through FastAPI.

The repository's existing Parrot memory-game files remain untouched. The new
backend is isolated in `shopping_api/`; this README describes the branch's
primary deliverable.

## Dataset and database design

The Drive file is a 4.3 KB CSV with 200 records and the source headers
`CustomerID`, `Genre`, `Age`, `Annual Income (k$)`, and
`Spending Score (1-100)`. The importer maps the source's `Genre` field to the
clearer API/database name `gender`. `CustomerID` is stored as `TEXT` so values
such as `0001` keep their leading zeroes.

SQLite keeps the project dependency-light and easy to run locally:

| Table | Column | Type and constraints |
| --- | --- | --- |
| `customers` | `customer_id` | `TEXT PRIMARY KEY` |
|  | `gender` | `TEXT NOT NULL`, `Male` or `Female` as present in the source |
|  | `age` | `INTEGER NOT NULL`, 0-120 |
|  | `annual_income_kusd` | `INTEGER NOT NULL`, non-negative, units are thousands of dollars |
|  | `spending_score` | `INTEGER NOT NULL`, 1-100 |
| `dataset_metadata` | `singleton_id` | one-row primary key constrained to `1` |
|  | source/import fields | source filename, Drive URL, source modification time, UTC import time, and row count |

Indexes support gender and numeric range filters. The importer validates the
exact source header, every value range, accepted gender values, duplicate IDs,
and an empty source before replacing the customer snapshot in one SQLite
transaction. The generated `shopping_api/data/shopping.db` and SQLite WAL
files are local runtime state and are intentionally ignored by Git; the CSV,
schema, and importer are versioned so the database is reproducible.

## Project layout

```text
shopping_api/
├── app/
│   ├── database.py          # read-only SQLite connection management
│   ├── main.py              # FastAPI endpoints, filters, and error handling
│   └── models.py            # validated response contracts
├── data/
│   └── Shopping_data.csv    # inspected Drive snapshot (200 data rows)
├── scripts/
│   └── import_data.py       # validation and transactional import CLI
├── tests/
│   └── test_api.py          # isolated API/import tests
└── schema.sql               # SQLite tables, checks, and indexes
```

## Local setup

Python 3.11 or newer is recommended.

```bash
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git switch prpl-ehi-shopping-api-dataset

python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies, import the persisted SQLite snapshot, and start the
server:

```bash
python -m pip install -r requirements.txt
python -m shopping_api.scripts.import_data
python -m uvicorn shopping_api.app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive OpenAPI docs are
at `http://127.0.0.1:8000/docs`. Set `SHOPPING_DB_PATH` before starting the
server or tests to use a different SQLite file.

## API operations

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Confirm that the database is readable and report its customer count |
| `GET` | `/api/v1/metadata` | Show the persisted dataset source and import metadata |
| `GET` | `/api/v1/customers` | List customers with stable ID ordering, pagination, filters, and search |
| `GET` | `/api/v1/customers/{customer_id}` | Fetch one four-digit customer ID or return `404` |

`GET /api/v1/customers` accepts:

- `page` (default `1`) and `page_size` (default `20`, maximum `100`)
- `gender=Male|Female`
- `age_min` / `age_max` (0-120)
- `income_min` / `income_max` (non-negative, in thousands of dollars)
- `score_min` / `score_max` (1-100)
- `q` (1-100 characters): a literal, case-insensitive substring search across
  customer ID, gender, age, income, and score; `%` and `_` are treated as text,
  not SQL wildcards

Filters, search, and pagination can be combined. All user values are bound SQL
parameters. Reversed ranges and invalid query values return `422`; a valid but
unknown customer returns `404`; an uninitialized or unreadable database returns
`503` with the import command needed to rebuild it.

## Usage examples

```bash
# First five records from the second page
curl "http://127.0.0.1:8000/api/v1/customers?page=2&page_size=5"

# Female customers aged 20-23 with a score of at least 50
curl "http://127.0.0.1:8000/api/v1/customers?gender=Female&age_min=20&age_max=23&score_min=50"

# Search all persisted fields
curl "http://127.0.0.1:8000/api/v1/customers?q=0199"

# Retrieve a single zero-padded customer ID
curl "http://127.0.0.1:8000/api/v1/customers/0001"

# Verify source lineage and import state
curl "http://127.0.0.1:8000/api/v1/metadata"
```

Example paginated response (abbreviated):

```json
{
  "items": [
    {
      "customer_id": "0006",
      "gender": "Female",
      "age": 22,
      "annual_income_kusd": 17,
      "spending_score": 76
    }
  ],
  "pagination": {
    "page": 2,
    "page_size": 5,
    "total": 200,
    "total_pages": 40,
    "has_previous": true,
    "has_next": true
  }
}
```

## Automated tests

Tests build an isolated SQLite database from the checked-in CSV and exercise
the API in process:

```bash
python -m pytest -q
```

## Known limitations and future improvements

- **Single-process local persistence.** SQLite is a good fit for this small,
  read-only dataset, but it is not the intended write-heavy, horizontally
  scaled production store. Add containerized deployment and a PostgreSQL path
  before enabling mutations or multiple API replicas.
- **No CI quality gate.** Local tests cover import, listing, pagination,
  filters, search, validation, and failure responses. Add GitHub Actions for
  tests, formatting/linting, type checks, and dependency/security scanning.
- **No public-API controls.** The current local read-only API has no
  authentication, authorization, rate limiting, or request telemetry. Add
  those controls before public or multi-tenant deployment.
- **Linear substring search and fixed ordering.** A 200-row table does not need
  a search engine, but larger datasets would benefit from SQLite FTS5 or
  PostgreSQL full-text indexes, explicit sort parameters, and relevance-aware
  results.

Those four scoped improvements are tracked as GitHub issues for this branch.
