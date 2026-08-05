# Shopping Customer API

A small, production-style Python REST API for exploring a 200-record shopping
customer dataset. The service validates the source CSV, imports it into a local
SQLite database, and exposes read-only customer listing, pagination, filtering,
search, and record lookup through FastAPI.

The source dataset is [`Shopping_data.csv` on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing).
It contains customer demographics, annual income in thousands of dollars, and a
spending score from 1 to 100. The Drive column named `Genre` is treated as gender
because its observed values are `Male` and `Female`.

## Database design

SQLite keeps local setup simple while providing transactions, constraints, and
indexes. Customer IDs are stored as `TEXT` so leading zeroes such as `0001` are
preserved.

| Column | SQLite type | Source field | Rules |
| --- | --- | --- | --- |
| `customer_id` | `TEXT` | `CustomerID` | Primary key; four-digit source ID |
| `gender` | `TEXT` | `Genre` | Required; `Male` or `Female` |
| `age` | `INTEGER` | `Age` | Required; 0–120 |
| `annual_income_kusd` | `INTEGER` | `Annual Income (k$)` | Required; non-negative |
| `spending_score` | `INTEGER` | `Spending Score (1-100)` | Required; 1–100 |

Indexes support the exposed filters on gender, age, income, and spending score.
The importer validates the complete file before opening its write transaction,
then replaces all records atomically by default. A failed validation therefore
does not leave a partial dataset behind.

## Project structure

```text
app/
├── config.py          # paths and SHOP_API_DATABASE configuration
├── database.py        # SQLite connection and schema creation
├── import_data.py     # CSV validation and transactional import CLI
├── main.py            # FastAPI application, routes, and error handlers
├── repository.py      # parameterized database queries
└── schemas.py         # response validation models
data/
└── shopping_customers.csv
tests/
├── conftest.py        # isolated temporary test database
└── test_api.py        # endpoint, filter, pagination, and error tests
```

The static game files already present on the repository's default branch are
left untouched; they are not used by this API.

## Requirements and setup

- Python 3.11 or newer
- Git

Clone the repository and select this branch:

```bash
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git switch 731-ceh-shopapi
```

Create a virtual environment and install the application plus test dependencies:

```bash
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Importing and persisting the data

Create `data/shop.db` and load all 200 customers:

```bash
python -m app.import_data
```

The command is safe to rerun: it validates the source file and replaces the
table contents in one transaction. Alternate paths are supported:

```bash
python -m app.import_data --dataset path/to/customers.csv --database path/to/shop.db
```

Use `--append` only when importing a dataset with new, non-duplicate IDs. Local
SQLite files are intentionally ignored by Git; every checkout can reproduce the
database from the tracked CSV.

To run the API against a different database, set `SHOP_API_DATABASE` before
starting the server:

```bash
# macOS/Linux
export SHOP_API_DATABASE=/absolute/path/to/shop.db

# Windows PowerShell
$env:SHOP_API_DATABASE = "C:\absolute\path\to\shop.db"
```

## Running the API

After importing the data:

```bash
python -m uvicorn app.main:app --reload
```

The service listens at `http://127.0.0.1:8000`. Interactive OpenAPI docs are at
`http://127.0.0.1:8000/docs` and the machine-readable schema is at
`http://127.0.0.1:8000/openapi.json`.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service links |
| `GET` | `/health` | Database reachability check |
| `GET` | `/customers` | Paginated list with filters and search |
| `GET` | `/customers/{customer_id}` | One customer by four-digit ID |

### Collection query parameters

| Parameter | Default | Validation / behavior |
| --- | --- | --- |
| `page` | `1` | Integer, at least 1 |
| `page_size` | `20` | Integer from 1 to 100 |
| `gender` | — | `Male` or `Female` |
| `min_age`, `max_age` | — | Integers from 0 to 120 |
| `min_annual_income`, `max_annual_income` | — | Non-negative integers, in k$ |
| `min_spending_score`, `max_spending_score` | — | Integers from 1 to 100 |
| `q` | — | Case-insensitive partial match on customer ID or gender; max 50 characters |

Minimum and maximum filters can be combined. A minimum greater than its matching
maximum returns `422 Unprocessable Entity`.

### Usage examples

List the first 20 customers:

```bash
curl "http://127.0.0.1:8000/customers"
```

Fetch the second page with five records:

```bash
curl "http://127.0.0.1:8000/customers?page=2&page_size=5"
```

Combine demographic and spending filters:

```bash
curl "http://127.0.0.1:8000/customers?gender=Female&min_age=30&max_age=40&min_spending_score=70"
```

Search for a customer ID and fetch one exact customer:

```bash
curl "http://127.0.0.1:8000/customers?q=0001"
curl "http://127.0.0.1:8000/customers/0001"
```

A collection response includes stable ID ordering and pagination metadata:

```json
{
  "items": [
    {
      "customer_id": "0001",
      "gender": "Male",
      "age": 19,
      "annual_income_kusd": 15,
      "spending_score": 39
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 200,
  "total_pages": 10
}
```

Validation and application errors use a consistent envelope:

```json
{
  "error": {
    "code": "invalid_range",
    "message": "min_age cannot exceed max_age."
  }
}
```

## Automated tests

Tests build an isolated temporary SQLite database from the real CSV and exercise
health, pagination, combined filters, search, lookup, and validation behavior:

```bash
python -m pytest
```

## Known limitations and future improvements

- The API is read-only and has no authentication, authorization, or rate limits.
- SQLite is appropriate for this local dataset, but concurrent production writes
  would benefit from PostgreSQL and a versioned migration tool such as Alembic.
- Search is intentionally small in scope because the dataset has no customer names
  or product text; it currently covers customer ID and gender only.
- There is no container image, hosted deployment configuration, request tracing,
  or metrics integration yet.
- CI is not configured to run tests and static checks automatically on pull requests.
