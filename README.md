# Shopping Customer API

A small read-only REST API for exploring the shopping customer dataset supplied through Google Drive. The project imports the CSV into a local SQLite database and exposes paginated listing, filtering, free-text search, and record lookup endpoints through FastAPI.

## Dataset

The source file is stored at `data/shopping.csv` and contains 200 customer records with these fields:

| CSV field | API/database field | Type | Notes |
| --- | --- | --- | --- |
| `CustomerID` | `customer_id` | text | Four-digit primary key; text preserves leading zeros |
| `Genre` | `gender` | text | Restricted to `Male` or `Female` to match the source data |
| `Age` | `age` | integer | Validated from 0 to 120 |
| `Annual Income (k$)` | `annual_income_k` | integer | Annual income in thousands of dollars |
| `Spending Score (1-100)` | `spending_score` | integer | Validated from 1 to 100 |

Source: [Google Drive dataset](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing).

## Database Design

SQLite is used because the dataset is small, local, and read-heavy. The `customers` table uses `customer_id` as its primary key and includes check constraints for field integrity. Indexes on gender, age, income, and spending score support the exposed filters. The importer uses an upsert, so it can be rerun without creating duplicates.

The generated database is `data/shopping.db`. It is intentionally ignored by Git because it can be recreated from the versioned CSV.

## Setup

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.import_data
```

The import command validates the CSV header and every row before writing. A different database location can be supplied with `--database` or the `SHOPPING_DB_PATH` environment variable.

## Run

```bash
uvicorn shopping_api.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

## API Usage

Check service and database status:

```bash
curl http://127.0.0.1:8000/health
```

List the second page with five records:

```bash
curl 'http://127.0.0.1:8000/customers?page=2&page_size=5'
```

Filter by gender, age, income, and spending score:

```bash
curl 'http://127.0.0.1:8000/customers?gender=Female&min_age=25&max_age=40&min_income=60&min_spending_score=70'
```

Search across customer ID, gender, age, income, and spending score:

```bash
curl 'http://127.0.0.1:8000/customers?q=0001'
```

Fetch one customer:

```bash
curl http://127.0.0.1:8000/customers/0001
```

Supported list parameters are `page`, `page_size`, `gender`, `min_age`, `max_age`, `min_income`, `max_income`, `min_spending_score`, `max_spending_score`, and `q`. Invalid values receive a `400` or `422` response; missing customers receive `404`.

## Tests

```bash
pytest
```

Tests create an isolated temporary SQLite database, import the source dataset, and exercise pagination, filtering/search, lookup, and validation behavior.

## Limitations and Future Improvements

- The service is read-only and has no authentication or authorization.
- Search uses SQLite `LIKE`; full-text search would scale better for larger datasets.
- SQLite is appropriate for local use but not for horizontally scaled deployments.
- Schema migrations, container packaging, CI, observability, and deployment configuration are not included.
- The source uses the column name `Genre` for gender; the API normalizes it to `gender` without inferring or expanding categories.
