# Shopping Customer Dataset API

A small production-style Python REST API for the shopping customer CSV
provided in Google Drive. The service imports the CSV into a local SQLite
database and exposes read-only endpoints for listing records, pagination,
filtering, search, and aggregate statistics.

Local working branch: `v1-mg-task002/sad`
Remote PR branch: `task002/shopping-api-dataset`

## Dataset

Source file:
`https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing`

Google Drive metadata inspected during implementation:

- File name: `Shopping_data.csv`
- MIME type: `text/csv`
- Modified: `2026-05-15T20:39:43.000Z`
- Rows: 200 customer records plus a header row

The Drive CSV is stored locally at `data/shopping.csv`.

### Columns

| CSV column | API / DB field | Type | Notes |
| --- | --- | --- | --- |
| `CustomerID` | `customer_id` | string | Four-digit customer identifier, stored with leading zeros |
| `Genre` | `genre` | string | `Female` or `Male`; the source file uses `Genre` rather than `Gender` |
| `Age` | `age` | integer | Customer age |
| `Annual Income (k$)` | `annual_income_k` | integer | Annual income in thousands |
| `Spending Score (1-100)` | `spending_score` | integer | Spending score from 1 to 100 |

## Database Design

The local database is SQLite by default, stored at `data/shopping.db`.
SQLAlchemy creates one denormalized table and a synchronized SQLite FTS5
virtual table:

`customers`

`customers_search`

| Column | Type | Constraints / indexes |
| --- | --- | --- |
| `id` | integer | Synthetic primary key |
| `customer_id` | string | Unique, indexed |
| `genre` | string | Indexed |
| `age` | integer | Used in range filters |
| `annual_income_k` | integer | Used in range filters |
| `spending_score` | integer | Used in range filters |

Additional indexes:

- `(genre, age)` for common demographic filtering
- `(annual_income_k, spending_score)` for segment-style range queries
- `customers_search` for ranked full-text search across customer id, genre,
  age, annual income, and spending score

A single table is appropriate here because the source data is small,
read-only, and already flat. Splitting lookup tables out for `genre`
would add joins without meaningful benefit at this size.

Schema definition lives in `app/models.py`. Import logic lives in
`app/import_data.py`.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Import Data

Create or refresh the SQLite database from the checked-in Drive CSV:

```bash
python -m app.import_data
```

Use another CSV path if needed:

```bash
python -m app.import_data path/to/Shopping_data.csv
```

Environment overrides:

- `SHOPPING_DATABASE_URL`: SQLAlchemy database URL, default `sqlite:///data/shopping.db`
- `SHOPPING_CSV_PATH`: CSV path used by the importer, default `data/shopping.csv`

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs are available at:

```text
http://localhost:8000/docs
```

## Tests

```bash
python -m pytest -q
```

The tests use an isolated temporary SQLite database, import
`data/shopping.csv`, and cover health checks, listing, pagination,
filtering, validation errors, search, single-record lookup, and stats.

## API Examples

### Health

```bash
curl http://localhost:8000/health
```

Response:

```json
{"status":"ok"}
```

### List Customers

```bash
curl "http://localhost:8000/customers?page=1&page_size=5"
```

Supported query parameters:

- `page`: integer, default `1`
- `page_size`: integer, default `20`, max `200`
- `genre`: `Female` or `Male`
- `min_age`, `max_age`
- `min_annual_income_k`, `max_annual_income_k`
- `min_spending_score`, `max_spending_score`

Example filtered query:

```bash
curl "http://localhost:8000/customers?genre=Female&min_annual_income_k=70&page_size=10"
```

Response shape:

```json
{
  "meta": {"total": 56, "page": 1, "page_size": 10, "pages": 6},
  "items": [
    {
      "id": 125,
      "customer_id": "0125",
      "genre": "Female",
      "age": 23,
      "annual_income_k": 70,
      "spending_score": 29
    }
  ]
}
```

### Get One Customer

```bash
curl http://localhost:8000/customers/0001
```

Returns `404` when the customer id does not exist.

### Search

Search matches `customer_id`, `genre`, `age`, `annual_income_k`, and
`spending_score` through SQLite FTS5 prefix search. Results are ordered by
BM25 relevance, then customer id for stable pagination.

```bash
curl "http://localhost:8000/search?q=Female&page_size=5"
```

### Genres

```bash
curl http://localhost:8000/genres
```

Response:

```json
["Female","Male"]
```

### Stats

```bash
curl http://localhost:8000/stats
```

Returns total customers, global averages and min/max values, plus a
per-genre breakdown.

## Validation And Error Handling

- Pagination parameters are validated by FastAPI and return `422` for invalid input.
- `genre` only accepts `Female` or `Male`.
- Spending score filters must stay within `1..100`.
- If a min filter is greater than its max filter, the API returns `400`.
- Unknown customer ids return `404`.
- The importer fails fast when required columns are missing or numeric cells are invalid.

## Known Limitations And Future Improvements

- The API is read-only. Future work could add create/update/delete endpoints.
- Search uses SQLite FTS5 prefix matching. Typo-tolerant matching is not enabled.
- There is no authentication or authorization.
- There is no rate limiting.
- The default database is SQLite. A Postgres profile would be better for concurrent deployments.
- Observability is minimal. Structured logs, request ids, and metrics should be added before production use.
- CI is not configured yet. A GitHub Actions workflow should run tests on every pull request.
- There is no container image or Compose file for repeatable deployment.
