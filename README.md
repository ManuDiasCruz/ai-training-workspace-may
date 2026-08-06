# Shopping Customer API

A small, production-style, read-only Python REST API for exploring a real
shopping customer dataset. FastAPI provides validated HTTP endpoints and
interactive OpenAPI documentation; SQLite stores the imported customer records
locally without requiring a separate database server.

The original source is
[Shopping_data.csv on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing).
A versioned copy is included at `data/Shopping_data.csv`, so application setup
does not require Google Drive credentials or an internet connection after Python
dependencies have been installed.

## Dataset

The source contains **200 customers** and five columns:

| Source column | Meaning | Observed values |
| --- | --- | --- |
| `CustomerID` | Four-digit, zero-padded customer identifier | `0001`–`0200` |
| `Genre` | Source dataset's gender/category column | 112 Female; 88 Male |
| `Age` | Customer age in years | 18–70 |
| `Annual Income (k$)` | Annual income in thousands of US dollars | 15–137 |
| `Spending Score (1-100)` | Original customer spending score | 1–99 |

The source column is named `Genre`, but its contents are `Female` and `Male`.
The API and database expose the clearer name `gender` while preserving the
original CSV and its values.

## Database design

SQLite persists the dataset in `data/shopping.sqlite3` by default. This generated
database and its temporary files are ignored by Git; rerun the import command to
recreate them locally.

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY
        CHECK (length(customer_id) = 4 AND customer_id NOT GLOB '*[^0-9]*'),
    gender TEXT NOT NULL CHECK (gender IN ('Female', 'Male')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k_usd INTEGER NOT NULL CHECK (annual_income_k_usd >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 0 AND 100)
);
```

`customer_id` is intentionally `TEXT`, preserving leading zeroes. Individual
indexes on `gender`, `age`, `annual_income_k_usd`, and `spending_score` support
the available filters. The importer validates the exact CSV headers, rejects
duplicate IDs and invalid values, and replaces existing rows in a single atomic
transaction.

## Requirements

- Python 3.10 or newer.
- `pip` and an internet connection for the initial dependency installation.

## Setup

Clone the repository and switch to the project branch:

```bash
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git switch 731-feh-shopapi
```

Create and activate a virtual environment.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Import the dataset

```bash
python -m shop_api.import_data
```

Expected output:

```text
Imported 200 customers into .../data/shopping.sqlite3.
```

The import can be rerun safely. To choose alternate files explicitly:

```bash
python -m shop_api.import_data --csv data/Shopping_data.csv --database data/custom.sqlite3
```

When using an alternate database, configure the same path for the API:

```bash
# macOS / Linux
export SHOP_API_DATABASE=data/custom.sqlite3

# Windows PowerShell
$env:SHOP_API_DATABASE = "data/custom.sqlite3"
```

## Run the API

```bash
python -m uvicorn shop_api.main:app --reload
```

The service listens at `http://127.0.0.1:8000`. Interactive Swagger
documentation is available at
[`/docs`](http://127.0.0.1:8000/docs), ReDoc at
[`/redoc`](http://127.0.0.1:8000/redoc), and the generated OpenAPI schema at
[`/openapi.json`](http://127.0.0.1:8000/openapi.json).

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Check database availability and report customer count. |
| `GET` | `/customers` | List customers with pagination, filters, and search. |
| `GET` | `/customers/{customer_id}` | Retrieve a customer by four-digit ID. |
| `GET` | `/stats` | Return gender counts and age/income/spending summaries. |

### List and paginate

```bash
curl "http://127.0.0.1:8000/customers?page=1&page_size=5"
```

Responses include both matching records and explicit pagination metadata:

```json
{
  "items": [
    {
      "customer_id": "0001",
      "gender": "Male",
      "age": 19,
      "annual_income_k_usd": 15,
      "spending_score": 39
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 5,
    "total_items": 200,
    "total_pages": 40,
    "has_next": true,
    "has_previous": false
  }
}
```

The default page size is 20, and the maximum is 100.

### Combine relevant filters

```bash
curl "http://127.0.0.1:8000/customers?gender=female&min_age=30&max_age=40&min_income=70&max_income=100&min_spending_score=60"
```

Supported query parameters:

- `gender`: `female` or `male`.
- `min_age` / `max_age`: inclusive age boundaries, from 0 to 120.
- `min_income` / `max_income`: inclusive income boundaries in thousands of USD.
- `min_spending_score` / `max_spending_score`: inclusive boundaries from 0 to 100.
- `page` / `page_size`: positive pagination controls.
- `q`: case-insensitive literal substring search across customer ID and gender.

### Search customers

```bash
curl "http://127.0.0.1:8000/customers?q=0001"
curl "http://127.0.0.1:8000/customers?q=female&page_size=10"
```

SQL wildcard characters supplied in `q` are escaped and treated literally.

### Fetch a customer

```bash
curl "http://127.0.0.1:8000/customers/0001"
```

### Check health and dataset statistics

```bash
curl "http://127.0.0.1:8000/health"
curl "http://127.0.0.1:8000/stats"
```

### Error handling

- Invalid pagination, unsupported filters, malformed customer IDs, or reversed
  numeric ranges return HTTP `422`.
- Unknown customer IDs return HTTP `404`.
- A missing, invalid, or empty database returns HTTP `503` with an actionable
  import instruction.
- Import failures exit with a nonzero status and do not overwrite an existing,
  valid dataset.

## Run automated tests

```bash
python -m pytest -q
```

The suite covers real imported data, pagination, combined filters, literal
case-insensitive search, customer lookup, aggregate statistics, invalid input,
missing databases, and preservation of existing records after a rejected import.

## Project structure

```text
data/
  Shopping_data.csv       Original versioned shopping dataset
  shopping.sqlite3        Generated local database; ignored by Git
shop_api/
  __init__.py             Application version
  database.py             SQLite connection, schema, and indexes
  import_data.py          Validated, atomic CSV import command
  main.py                 FastAPI endpoints and query behavior
  schemas.py              Typed public API response models
tests/
  test_api.py             Automated API and import tests
requirements.txt          Runtime and test dependencies
```

The repository also contains pre-existing browser-game assets inherited from its
default branch; those files are unrelated to this backend project and are left
unchanged.

## Known limitations and future improvements

- The API is intentionally read-only and does not provide authentication,
  authorization, or rate limiting.
- SQLite is suitable for local development but is not a multi-instance
  production database; PostgreSQL and migrations would improve scalability.
- Search currently scans customer IDs and gender with `LIKE`; SQLite FTS5 or a
  dedicated search backend would support richer indexed search.
- Dependency versions are bounded but not locked, and no automated GitHub
  Actions quality pipeline is configured.
- Imports currently replace the complete dataset; larger or regularly refreshed
  feeds could benefit from streaming ingestion, incremental upserts, and import
  audit history.
- Gender values mirror the historical source dataset; broader real-world data
  should use a more inclusive, source-specific taxonomy.
