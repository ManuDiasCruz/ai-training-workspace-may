# Shopping Customer API

A small production-style Python REST API backed by SQLite. It imports the
200-row `Shopping_data.csv` snapshot from Google Drive and exposes deterministic
pagination, filters, search, record lookup, health checks, validation, and
OpenAPI documentation.

## Dataset

Source: [Shopping_data.csv on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing)

The source file contains these columns:

| CSV column | Meaning | SQLite column |
| --- | --- | --- |
| `CustomerID` | Four-character customer identifier | `customer_id` |
| `Genre` | Source-provided customer category (`Male` or `Female`) | `genre` |
| `Age` | Age in years | `age` |
| `Annual Income (k$)` | Annual income in thousands of dollars | `annual_income_kusd` |
| `Spending Score (1-100)` | Source-provided spending score | `spending_score` |

`customer_id` is stored as `TEXT`, preserving source identifiers such as
`0001`. The API intentionally retains the source column name `genre` rather
than silently changing its semantics.

## Database design

SQLite keeps setup local and dependency-free. The importer creates one table:

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    genre TEXT NOT NULL CHECK (genre IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_kusd INTEGER NOT NULL CHECK (annual_income_kusd >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100),
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Indexes on `genre`, `age`, `annual_income_kusd`, and `spending_score` support
the available filters. Import is transactional and repeatable: existing rows
are updated by `customer_id`, so reruns do not duplicate data. The generated
`data/shopping.db` is excluded from Git because it is reproducibly built from
the versioned CSV snapshot.

## Setup

From this `shopping-api` directory, create and activate a virtual environment:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -r requirements-dev.txt
```

Python 3.10 or newer is required.

## Import and run

Create `data/shopping.db` and persist the CSV rows:

```bash
python -m scripts.import_data
```

Optional locations can be supplied explicitly:

```bash
python -m scripts.import_data --csv path/to/input.csv --database path/to/shopping.db
```

Start the development server:

```bash
uvicorn shopping_api.main:app --reload
```

The app will also initialize the schema and import the bundled CSV automatically
when its default database is empty. Set `SHOPPING_DATABASE` and `SHOPPING_CSV`
to override the runtime paths. Interactive docs are available at
<http://127.0.0.1:8000/docs> and the OpenAPI document at
<http://127.0.0.1:8000/openapi.json>.

## API

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### List and paginate customers

```bash
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"
```

The response contains `items`, `page`, `page_size`, `total`, and `pages`.
`page` starts at 1 and `page_size` must be between 1 and 100.

### Filter records

All filters can be combined:

```bash
curl "http://127.0.0.1:8000/customers?genre=female&min_age=25&max_age=40&min_annual_income=60&max_spending_score=90"
```

Supported filters are `genre`, `min_age`, `max_age`,
`min_annual_income`, `max_annual_income`, `min_spending_score`, and
`max_spending_score`. Impossible reversed ranges return HTTP 400; invalid or
out-of-bound query values return FastAPI's HTTP 422 validation response.

### Search

Search is case-insensitive across customer ID and genre:

```bash
curl "http://127.0.0.1:8000/customers?search=019"
```

### Fetch one customer

```bash
curl http://127.0.0.1:8000/customers/0001
```

Unknown IDs return HTTP 404 with `{"detail":"Customer not found"}`.

## Tests

Run the automated API test suite from this directory:

```bash
python -m pytest -q
```

The test imports the source CSV into an isolated temporary database and checks
pagination, combined filtering and search, range validation, and 404 handling.

## Limitations and future improvements

- The repository contains a static source snapshot; scheduled Drive sync and
  source checksum/audit metadata would improve provenance.
- Offset pagination is simple for 200 rows but should become cursor-based for a
  large or frequently updated table.
- Search uses SQLite `LIKE` across ID and genre only; SQLite FTS or an external
  search engine would support richer queries.
- The service is read-only and has no authentication, rate limiting, metrics,
  or production deployment/container configuration.
- The source `Genre` field is limited to `Male`/`Female`; a future data contract
  should clarify meaning and support broader values where available.
