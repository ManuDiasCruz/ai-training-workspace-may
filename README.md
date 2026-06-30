# Shopping Dataset API

A small, production-style, read-only REST API for exploring the customer
shopping dataset stored in Google Drive. The project validates the source CSV,
persists its 200 records in SQLite, and exposes deterministic pagination,
filtering, search, health, and record lookup operations through FastAPI.

- Source dataset: [Shopping_data.csv on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing)
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Alternative OpenAPI documentation: `http://127.0.0.1:8000/redoc`

## Dataset summary

The source contains 200 customer rows with no duplicate customer IDs. Its
original `Genre` heading contains gender values, so the importer deliberately
normalizes that field to `gender` while preserving the source CSV unchanged.

| Source field | API/database field | Type and observed range |
| --- | --- | --- |
| `CustomerID` | `customer_id` | Four-character numeric string, `0001`-`0200` |
| `Genre` | `gender` | `Female` or `Male` |
| `Age` | `age` | Integer, 18-70 |
| `Annual Income (k$)` | `annual_income_k` | Integer, 15-137 (thousands of USD) |
| `Spending Score (1-100)` | `spending_score` | Integer, 1-99 in this dataset |

## Database design

SQLite keeps local setup lightweight and preserves IDs with leading zeros.
The single-table schema is appropriate because each CSV row describes one
customer and the dataset contains no repeating child entities.

| Column | SQLite type | Rules |
| --- | --- | --- |
| `customer_id` | `TEXT` | Primary key; exactly four numeric characters |
| `gender` | `TEXT` | Required; `Female` or `Male` |
| `age` | `INTEGER` | Required; 0-120 |
| `annual_income_k` | `INTEGER` | Required; non-negative |
| `spending_score` | `INTEGER` | Required; 1-100 |

Indexes on `gender`, `age`, `annual_income_k`, and `spending_score` support the
available filters. All queries use bound parameters. The importer validates the
complete input first, then upserts all rows in one transaction, so rerunning it
is safe and does not create duplicates.

The generated `data/shopping.db` is intentionally ignored by Git. It is created
locally from the versioned source CSV, making the persisted data reproducible
without committing a machine-generated binary file.

## Project structure

```text
app/
  database.py       SQLite schema and connection helpers
  main.py           FastAPI application and request validation
  models.py         Response models
  repository.py     Parameterized read queries
data/
  Shopping_data.csv Original Drive dataset
scripts/
  init_db.py        Validating, idempotent CSV importer
tests/
  test_api.py       API integration tests using a temporary database
requirements.txt
requirements-dev.txt
```

## Setup

Python 3.10 or newer is required.

```bash
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git switch red-shopping-api-dataset

python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies and build the local database:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m scripts.init_db
```

The import command should report:

```text
Imported 200 customers into data/shopping.db
```

To use different files, pass explicit paths:

```bash
python -m scripts.init_db --csv path/to/input.csv --database path/to/shopping.db
```

## Run the API

```bash
uvicorn app.main:app --reload
```

The default database is `data/shopping.db`. Override it when needed:

```bash
# macOS/Linux
SHOPPING_DATABASE_PATH=/path/to/shopping.db uvicorn app.main:app

# Windows PowerShell
$env:SHOPPING_DATABASE_PATH = "C:\path\to\shopping.db"
uvicorn app.main:app
```

## API endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Service links |
| `GET` | `/health` | Database readiness and persisted record count |
| `GET` | `/customers` | Paginated list with optional filters and search |
| `GET` | `/customers/{customer_id}` | One customer by four-digit source ID |

### List and paginate

```bash
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"
```

Responses keep pagination metadata separate from records:

```json
{
  "items": [
    {
      "customer_id": "0011",
      "gender": "Male",
      "age": 67,
      "annual_income_k": 19,
      "spending_score": 14
    }
  ],
  "pagination": {
    "page": 2,
    "page_size": 10,
    "total_items": 200,
    "total_pages": 20
  }
}
```

`page` starts at 1. `page_size` defaults to 20 and is limited to 100.

### Filter records

Filters may be combined:

```bash
curl "http://127.0.0.1:8000/customers?gender=Female&min_age=25&max_age=40&min_income=70&max_income=100&min_spending_score=60"
```

Supported filters are:

- `gender`: `Female` or `Male`
- `min_age`, `max_age`: 0-120
- `min_income`, `max_income`: non-negative values in thousands of USD
- `min_spending_score`, `max_spending_score`: 1-100

Minimum values cannot exceed their corresponding maximums. Invalid parameters
return a `422` response with details.

### Search

`search` performs a case-insensitive partial match on customer ID or gender:

```bash
curl "http://127.0.0.1:8000/customers?search=0194"
curl "http://127.0.0.1:8000/customers?search=fem&page_size=5"
```

SQL wildcard characters are treated as literal text.

### Retrieve one customer

```bash
curl "http://127.0.0.1:8000/customers/0001"
```

Unknown IDs return `404`; malformed IDs return `422`.

## Automated tests

```bash
python -m pytest -q
```

The tests import the versioned CSV into a temporary SQLite database and cover
health, pagination, combined filters, search, record lookup, not-found handling,
and invalid inputs. They do not modify the developer's local database.

## Known limitations and future improvements

- SQLite and synchronous access suit a local, read-heavy demo but not a
  horizontally scaled service. A future version could use PostgreSQL,
  SQLAlchemy, and Alembic migrations.
- Import is an explicit local command. A scheduled, checksum-aware refresh
  pipeline could ingest changed Drive files and retain provenance metadata.
- Search is intentionally limited to customer ID and gender. Full-text search,
  sortable result fields, and aggregate/segment endpoints would make larger
  datasets more useful.
- The read-only public API has no authentication, rate limiting, structured
  telemetry, container image, or continuous-integration workflow. Those should
  be added before internet-facing deployment.
