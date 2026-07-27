# Shopping Customer API

A small production-style Python REST API for exploring the customer shopping
dataset stored in Google Drive. The project validates the source CSV, persists
its 200 records in a local SQLite database, and exposes paginated listing,
field filters, sorting, basic search, single-record lookup, and health checks.

Source dataset: [Shopping_data.csv](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing)

## Dataset profile

The source contains one row per customer and five columns:

| Source column | Stored field | Observed values |
| --- | --- | --- |
| `CustomerID` | `customer_id` | `0001`–`0200` |
| `Genre` | `genre` | `Female`, `Male` |
| `Age` | `age` | 18–70 |
| `Annual Income (k$)` | `annual_income_k` | 15–137 |
| `Spending Score (1-100)` | `spending_score` | 1–99 |

Customer IDs are stored as text to preserve leading zeros. The API retains the
source label `genre` for traceability, although the values represent a binary
gender field in this dataset.

## Database design

SQLite keeps local setup lightweight while still providing transactions,
constraints, indexes, and durable persistence. The generated database is
`data/shopping.db` and is intentionally ignored by Git because it can be
recreated deterministically from the committed source CSV.

### `customers`

| Column | Type | Rules |
| --- | --- | --- |
| `customer_id` | `TEXT` | Primary key; preserves four-digit IDs |
| `genre` | `TEXT` | Required; `Male` or `Female` |
| `age` | `INTEGER` | Required; 0–120 |
| `annual_income_k` | `INTEGER` | Required; non-negative, in k$ |
| `spending_score` | `INTEGER` | Required; 1–100 |
| `imported_at` | `TEXT` | UTC timestamp supplied by SQLite |

Indexes support the available filters on genre, age, annual income, and
spending score. Imports use an upsert keyed by `customer_id`, so rerunning the
command safely refreshes existing rows instead of duplicating them.

### `dataset_imports`

Each successful import records the source filename, SHA-256 checksum, row
count, and import time. This small audit table makes the local database's source
and refresh history inspectable.

## Project structure

```text
app/
├── database.py       # connection settings and SQLite schema
├── import_data.py    # CSV validation and idempotent import CLI
├── main.py           # FastAPI application and HTTP validation
├── models.py         # response models
└── repository.py     # parameterized read queries
data/
└── Shopping_data.csv # source snapshot downloaded from Google Drive
tests/
└── test_api.py       # automated API tests using an isolated database
requirements.txt
```

The repository's earlier static-game files remain in this branch for history,
but they are not used by the API.

## Local setup

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Import and run

From the repository root, validate the CSV and build the local database:

```bash
python -m app.import_data
```

Expected output:

```text
Imported 200 rows into .../data/shopping.db (200 rows total).
```

Start the development server:

```bash
python -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive OpenAPI
documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Set `SHOP_API_DB_PATH` to point the running API at a different SQLite file.
The importer also accepts explicit paths:

```bash
python -m app.import_data --csv data/Shopping_data.csv --database data/custom.db
```

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Confirm database availability and row count |
| `GET` | `/customers` | List, paginate, filter, search, and sort records |
| `GET` | `/customers/{customer_id}` | Fetch one four-digit customer ID |

### Listing and pagination

```bash
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"
```

The response includes `items`, `page`, `page_size`, `total`, and `pages`.
`page` must be at least 1 and `page_size` must be between 1 and 100.

### Filtering

`GET /customers` supports these optional filters:

| Parameter | Validation |
| --- | --- |
| `genre` | `Male` or `Female`, case-insensitive |
| `min_age`, `max_age` | 0–120; minimum cannot exceed maximum |
| `min_annual_income`, `max_annual_income` | Non-negative k$ values |
| `min_spending_score`, `max_spending_score` | 1–100 |

Example:

```bash
curl "http://127.0.0.1:8000/customers?genre=Female&min_age=30&max_age=40&min_spending_score=70&page_size=20"
```

### Search and sorting

`q` performs a case-insensitive partial search on customer ID and genre.
Wildcard characters are treated literally. Results can be sorted by
`customer_id`, `age`, `annual_income_k`, or `spending_score` in `asc` or `desc`
order.

```bash
curl "http://127.0.0.1:8000/customers?q=019&sort_by=annual_income_k&sort_order=desc"
```

### Single record

```bash
curl "http://127.0.0.1:8000/customers/0001"
```

Unknown customers return `404`. Invalid paths, pagination values, filter
ranges, and field values return structured `422` responses. Unexpected SQLite
errors return a generic `500` response without exposing database details.

## Tests

Run the automated suite from the repository root:

```bash
python -m pytest -q
```

The tests create an isolated temporary SQLite database and cover combined
pagination/filter/search behavior, sorting, single-record lookup, not-found
handling, range validation, and health reporting.

## Known limitations and future improvements

- SQLite is appropriate for local exploration, but there are no migrations or
  production PostgreSQL configuration yet.
- The API is read-only and has no authentication, authorization, or rate
  limiting.
- Search is intentionally basic and limited to customer ID and genre; there is
  no full-text or fuzzy search.
- There are no analytical aggregation or customer-segmentation endpoints.
- Packaging currently targets local execution; containerization, CI checks,
  deployment configuration, metrics, and structured request logging are not
  included.
- The source offers only a small, static, binary demographic sample. Its field
  taxonomy and representation should not be generalized to other datasets.
