# Shopping Customer REST API

A small, production-style Python REST API for exploring the shopping customer
dataset supplied through Google Drive. The project validates and imports the
source CSV into SQLite, then exposes read-only customer listing, pagination,
filtering, search, and individual lookup operations through FastAPI.

Source dataset: [Shopping_data.csv](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing)

## What is included

- Reproducible, idempotent CSV-to-SQLite import.
- Database constraints and indexes for the source fields.
- Automatic database creation and first-run seeding.
- Paginated customer listing with composable filters.
- Case-insensitive search by customer ID or gender.
- FastAPI/OpenAPI input validation and documented error responses.
- Isolated automated API tests using a temporary database.

## Dataset summary

The source contains 200 records and no missing values. `CustomerID` is stored
as text so its leading zeroes are not lost.

| Source column | Database column | SQLite type | Observed range / values |
| --- | --- | --- | --- |
| `CustomerID` | `customer_id` | `TEXT PRIMARY KEY` | `0001`-`0200` |
| `Genre` | `gender` | `TEXT NOT NULL` | `Male`, `Female` |
| `Age` | `age` | `INTEGER NOT NULL` | 18-70 |
| `Annual Income (k$)` | `annual_income_kusd` | `INTEGER NOT NULL` | 15-137 |
| `Spending Score (1-100)` | `spending_score` | `INTEGER NOT NULL` | 1-99 |

The source label `Genre` is treated as a gender field because its values are
`Male` and `Female`.

## Database design

The local database is `data/shopping.db` and contains one `customers` table:

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY
        CHECK (customer_id GLOB '[0-9][0-9][0-9][0-9]'),
    gender TEXT NOT NULL
        CHECK (gender IN ('Male', 'Female')),
    age INTEGER NOT NULL
        CHECK (age BETWEEN 0 AND 120),
    annual_income_kusd INTEGER NOT NULL
        CHECK (annual_income_kusd >= 0),
    spending_score INTEGER NOT NULL
        CHECK (spending_score BETWEEN 1 AND 100)
);
```

Separate indexes on `gender`, `age`, `annual_income_kusd`, and
`spending_score` support the API filters. Import validation happens before the
transaction starts, and an import either succeeds completely or leaves the
existing data intact. Re-imports upsert by `customer_id`; `--replace` performs
a full refresh. The generated database and its WAL files are intentionally
ignored by Git, while the source CSV is versioned for reproducible local setup.

## Project structure

```text
app/
  database.py       SQLite schema, connection, validation, and import logic
  main.py           FastAPI app factory, routes, validation, and error handling
  models.py         Public response models
  repository.py     Parameterized customer queries
data/
  Shopping_data.csv Versioned source dataset
scripts/
  import_data.py    Database import command
tests/
  test_api.py       End-to-end tests with an isolated SQLite database
requirements.txt
requirements-dev.txt
```

The repository's pre-existing static game files remain unchanged and are not
used by this backend API.

## Setup

Python 3.11 or newer is recommended.

```bash
git switch cyn-ehi-shopping-api-dataset
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install runtime and test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

## Import and execution

Create or fully refresh the local SQLite database:

```bash
python -m scripts.import_data --replace
```

The command should report 200 imported customer records. Importing manually is
optional: the API creates the schema and seeds an empty database from the CSV
at startup.

Start the development server:

```bash
python -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive documentation is
available at `http://127.0.0.1:8000/docs`, with the OpenAPI document at
`http://127.0.0.1:8000/openapi.json`.

## API usage

### Health and record count

```bash
curl "http://127.0.0.1:8000/health"
```

```json
{"status":"ok","records":200}
```

### List and paginate customers

```bash
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"
```

The response contains `items`, `page`, `page_size`, `total`, and
`total_pages`. Results are ordered by `customer_id` for stable pagination.

### Filter customers

All filters can be combined:

```bash
curl "http://127.0.0.1:8000/customers?gender=Female&age_min=25&age_max=35&income_min=60&score_min=70&page_size=25"
```

| Query parameter | Validation | Meaning |
| --- | --- | --- |
| `page` | integer, at least 1 | 1-based result page |
| `page_size` | integer, 1-100 | records per page |
| `gender` | `Male` or `Female` | exact source-category match |
| `age_min`, `age_max` | integer, 0-120 | inclusive age range |
| `income_min`, `income_max` | non-negative integer | inclusive annual income range in k$ |
| `score_min`, `score_max` | integer, 1-100 | inclusive spending-score range |
| `search` | 1-50 characters | customer ID or gender substring |

### Search

```bash
curl "http://127.0.0.1:8000/customers?search=0001"
```

Search is case-insensitive and safely escapes SQL wildcard characters.

### Fetch one customer

```bash
curl "http://127.0.0.1:8000/customers/0001"
```

```json
{
  "customer_id": "0001",
  "gender": "Male",
  "age": 19,
  "annual_income_kusd": 15,
  "spending_score": 39
}
```

Invalid query values and reversed ranges return `422`. A well-formed customer
ID that does not exist returns `404`. Database errors are logged server-side
and returned as a generic `500` response without exposing internal details.

## Tests

Run the automated suite from the repository root:

```bash
python -m pytest
```

The tests verify database initialization, the health endpoint, pagination,
combined filters, search, customer lookup, validation, and not-found handling.

## Known limitations and future improvements

- The API is read-only; it does not create, update, or delete customers.
- SQLite is appropriate for this local dataset but not for high-concurrency or
  multi-instance deployments; PostgreSQL and migrations would be a natural
  next step.
- Search is limited to customer ID and gender because the dataset has no names
  or descriptive text. Larger datasets could use SQLite FTS or a search service.
- The fixed source values only represent two gender categories and should not
  be generalized beyond this dataset without revisiting the model.
- Authentication, authorization, rate limiting, structured observability, and
  deployment/container configuration are outside the current scope.
- Tests cover the primary success and validation paths but not performance,
  security, or malformed-source fuzzing.
