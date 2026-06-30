# Shopping Dataset REST API

A small, production-style Python REST API that imports a 200-row customer shopping dataset from Google Drive into SQLite and exposes it through validated, read-only endpoints. The original repository's front-end assets are left in place; the backend application for this branch is contained in [shopping_api](shopping_api).

## Dataset

Source: [Shopping_data.csv on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing)

The CSV contains 200 customer records and these source columns:

| Source column | Database/API field | Type and rules |
| --- | --- | --- |
| CustomerID | customer_id | Four-digit text primary key (keeps leading zeroes) |
| Genre | gender | Male or Female (the original dataset appears to use “Genre” for gender) |
| Age | age | Integer, 0–120 |
| Annual Income (k$) | annual_income_k | Non-negative integer, thousands of USD |
| Spending Score (1-100) | spending_score | Integer, 1–100 |

The checked-in copy is at shopping_api/data/Shopping_data.csv, so setup does not require Drive access.

## Database design

The app uses one normalized SQLite table because each source row represents one customer and the dataset has no repeating groups or relationships that warrant additional tables.

~~~sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY CHECK (...four digits...),
    gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);
~~~

Indexes on gender, age, annual_income_k, and spending_score support the API's filters. The import command validates headers and values, rejects duplicate IDs, and applies all inserts/upserts in one transaction.

## Local setup

Python 3.10 or later is recommended.

~~~bash
cd shopping_api
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
~~~

Create the local database and import the CSV:

~~~bash
python -m app.import_data
~~~

By default this reads data/Shopping_data.csv and writes data/shopping.db. Both paths can be overridden:

~~~bash
python -m app.import_data --csv path/to/file.csv --db path/to/shopping.db
~~~

The importer is idempotent: running it again upserts the source rows. Use --replace to clear the table first.

## Run the API

From shopping_api/:

~~~bash
python -m uvicorn app.main:app --reload
~~~

The API is served at http://127.0.0.1:8000. Interactive OpenAPI documentation is at /docs and the schema is at /openapi.json. Set SHOPPING_DB_PATH to use a different SQLite file.

## API usage

### Health and record lookup

~~~bash
curl "http://127.0.0.1:8000/health"
curl "http://127.0.0.1:8000/customers/0001"
~~~

### Listing and pagination

~~~bash
curl "http://127.0.0.1:8000/customers?page=2&page_size=10"
~~~

A list response includes items, total, page, page_size, total_pages, and has_next.

### Filters

All filters are optional and can be combined:

~~~bash
curl "http://127.0.0.1:8000/customers?gender=Female&min_age=25&max_age=35"
curl "http://127.0.0.1:8000/customers?min_income=70&max_income=100&min_spending_score=75"
~~~

Supported filters: gender, min_age, max_age, min_income, max_income, min_spending_score, and max_spending_score. Invalid ranges return HTTP 422.

### Search

Search performs a case-insensitive partial match across customer ID and gender:

~~~bash
curl "http://127.0.0.1:8000/customers?search=001"
curl "http://127.0.0.1:8000/customers?search=female&page_size=5"
~~~

## Automated tests

~~~bash
cd shopping_api
python -m pytest
~~~

The tests create an isolated temporary database and cover import persistence, pagination, combined filters/search, single-record lookup, missing-record handling, and invalid input.

## Project structure

~~~text
shopping_api/
├── app/
│   ├── db.py           # SQLite schema and connection helper
│   ├── import_data.py  # Validated, transactional CSV importer
│   └── main.py         # FastAPI application and endpoints
├── data/
│   └── Shopping_data.csv
├── tests/
│   └── test_api.py
├── pyproject.toml
└── requirements.txt
~~~

## Known limitations and future improvements

- This version intentionally offers a read-only API with no authentication or authorization.
- SQLite is appropriate for a small local dataset, but production deployments should use a managed database with migrations and connection pooling.
- Search is a simple SQL substring match; full-text search or typed field-specific search would be more scalable and expressive.
- The app does not yet expose aggregate analytics, bulk imports through the API, or background data-refresh jobs.
- The source's Genre header is mapped to gender for clarity, but demographic terminology and allowed values should be verified with the dataset owner.
- The dataset's provenance and license should be documented before redistribution or production use.
