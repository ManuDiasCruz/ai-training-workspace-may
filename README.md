# Shopping Dataset API

A small production-style, read-only REST API for exploring a customer shopping
dataset. The project validates the original CSV, persists its 200 rows in a
local SQLite database, and exposes paginated listing, filters, basic search,
single-record lookup, and health endpoints through FastAPI.

Source dataset: [Shopping_data.csv on Google Drive](https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view?usp=sharing).
The source names its gender-like categorical column `Genre`; this API preserves
that source terminology as `genre` instead of silently changing its meaning.

## Database design

SQLite keeps local setup lightweight while still providing transactions,
constraints, and useful query indexes. The generated `data/shopping.db` is
ignored by Git: `data/Shopping_data.csv` is the reproducible source of truth.

```text
customers
├── customer_id       TEXT PRIMARY KEY (exactly four digits)
├── genre             TEXT NOT NULL ('Female' or 'Male')
├── age               INTEGER NOT NULL (0–120)
├── annual_income_k   INTEGER NOT NULL (>= 0, thousands of dollars)
└── spending_score    INTEGER NOT NULL (1–100)
```

Indexes cover `genre`, `age`, `annual_income_k`, and `spending_score`. The
importer verifies the exact CSV headers, value ranges, allowed genres, and
duplicate IDs before an upsert is attempted. `--replace` provides a clean,
repeatable rebuild.

## Requirements and setup

- Python 3.10 or newer
- No external database server

```bash
git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may
git switch yellow-shopping-api-dataset

python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -r requirements-dev.txt
```

To keep the runtime installation smaller when tests are not needed, install
`requirements.txt` instead.

## Importing and running

Create or rebuild the local database explicitly:

```bash
python -m shopping_api.import_data --replace
# Imported 200 rows into .../data/shopping.db
```

Then start the development server:

```bash
python -m uvicorn shopping_api.app:app --reload
```

The service is available at `http://127.0.0.1:8000`; interactive OpenAPI
documentation is at `http://127.0.0.1:8000/docs`. If the database is missing or
empty, application startup automatically creates the schema and imports the
CSV. Set `SHOPPING_DB_PATH` to use a different database location.

Run the automated tests with:

```bash
python -m pytest -q
```

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service and documentation links |
| `GET` | `/health` | Database health and persisted row count |
| `GET` | `/customers` | Paginated customer listing, filters, and search |
| `GET` | `/customers/{customer_id}` | One customer by four-digit ID |

`GET /customers` accepts:

- `page` (default `1`) and `page_size` (default `20`, maximum `100`)
- `genre`: exactly `Female` or `Male`
- `age_min`, `age_max` (0–120)
- `income_min`, `income_max` (non-negative, in thousands of dollars)
- `score_min`, `score_max` (1–100)
- `q`: case-insensitive literal substring search across all five fields

Minimum values may not exceed their paired maximums. Invalid inputs return
HTTP 422, missing customers return HTTP 404, and database failures return a
generic HTTP 500 message without leaking implementation details.

## Usage examples

List the first 10 customers:

```bash
curl "http://127.0.0.1:8000/customers?page=1&page_size=10"
```

Find male customers aged 60–70 with a spending score of at least 40:

```bash
curl "http://127.0.0.1:8000/customers?genre=Male&age_min=60&age_max=70&score_min=40"
```

Search all fields for a literal substring:

```bash
curl "http://127.0.0.1:8000/customers?q=0001"
```

Fetch one record:

```bash
curl "http://127.0.0.1:8000/customers/0001"
```

Example paginated response shape:

```json
{
  "items": [
    {
      "customer_id": "0001",
      "genre": "Male",
      "age": 19,
      "annual_income_k": 15,
      "spending_score": 39
    }
  ],
  "page": 1,
  "page_size": 1,
  "total": 200,
  "pages": 200
}
```

## Known limitations and future improvements

- Search uses escaped SQL `LIKE` clauses and fixed customer-ID ordering. A
  future iteration could add FTS5, explicit sort controls, and relevance
  ranking.
- SQLite is well suited to this small local dataset, but there is no migration
  system or stored dataset-version/import audit metadata yet.
- The API is read-only and intentionally has no authentication, authorization,
  rate limiting, container image, or production deployment configuration.
- Dataset exploration is limited to raw records. Aggregate/statistical
  endpoints would make income, age, genre, and spending-score patterns easier
  to consume.
