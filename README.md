# Shopping Dataset API

A small production-style Python REST API over a shopping/retail dataset.
It loads a CSV into a local SQLite database and exposes read-only
endpoints with pagination, filtering, search, and aggregate stats.

> Branch: `task002/shopping-api-dataset`

## Dataset

The task referenced a dataset hosted on Google Drive
(`1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm`). That host is not reachable from
the sandboxed environment this branch was developed in (the
environment's network policy denies `drive.google.com`), so a
deterministic sample CSV mirroring the well-known **Customer Shopping
Trends** schema is generated at `data/shopping.csv` via
`scripts/generate_sample_dataset.py`.

To swap in the real CSV: drop it at `data/shopping.csv` and rerun the
importer. The importer normalizes headers, so both the Kaggle-style
columns (e.g. `Purchase Amount (USD)`, `Item Purchased`) and the
snake_case variant produced by the generator are accepted.

### Columns

| Field | Type | Notes |
| --- | --- | --- |
| `customer_id` | int | Customer identifier |
| `age` | int | Customer age |
| `gender` | string | Male / Female |
| `item_purchased` | string | Product name |
| `category` | string | Clothing / Footwear / Accessories / Outerwear |
| `purchase_amount_usd` | float | Transaction amount in USD |
| `location` | string | US state |
| `size` | string | XS / S / M / L / XL |
| `color` | string | Free text |
| `season` | string | Spring / Summer / Fall / Winter |
| `review_rating` | float | 0.0 – 5.0 |
| `subscription_status` | string | Yes / No |
| `payment_method` | string | Card / PayPal / etc. |
| `shipping_type` | string | Standard / Express / etc. |
| `discount_applied` | string | Yes / No |
| `promo_code_used` | string | Yes / No |
| `previous_purchases` | int | Lifetime count |
| `frequency_of_purchases` | string | Weekly / Monthly / etc. |

## Database design

Single SQLite table `purchases` with a synthetic `id` primary key
(autoincrement) and indexes on the columns most useful for filtering:

- `customer_id`
- `gender`
- `item_purchased`
- `category`
- `location`
- `season`
- composite `(category, location)`

A single denormalized table is intentional — the dataset is read-only,
under a million rows, and most queries are single-entity scans with
simple filters. A star schema would add operational cost (multiple
tables, joins) with no real query benefit at this scale.

Schema definition lives in `app/models.py`. Tables are created on
startup via SQLAlchemy `create_all`.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

1. (Optional) regenerate the sample dataset:

   ```bash
   python scripts/generate_sample_dataset.py
   ```

2. Import the CSV into SQLite (creates `data/shopping.db`):

   ```bash
   python -m app.import_data
   # or with a custom CSV path:
   python -m app.import_data path/to/your.csv
   ```

3. Start the API:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. Browse the interactive docs at `http://localhost:8000/docs`.

Environment overrides:

- `SHOPPING_DATABASE_URL` — any SQLAlchemy URL (defaults to local SQLite).
- `SHOPPING_CSV_PATH` — alternate CSV location.

## Tests

```bash
python -m pytest -q
```

The test suite spins up an isolated SQLite DB in a temp dir, imports
the sample CSV into it, and exercises every endpoint (pagination,
filters, validation errors, search, single-record 404, stats).

## API usage

### `GET /health`

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### `GET /purchases` — list with pagination & filters

Query params:

- `page` (default `1`)
- `page_size` (default `20`, max `200`)
- `category`, `gender`, `location`, `season`
- `min_amount`, `max_amount`
- `min_rating` (0–5)

```bash
curl "http://localhost:8000/purchases?category=Footwear&min_rating=4&page_size=5"
```

Response shape:

```json
{
  "meta": {"total": 137, "page": 1, "page_size": 5, "pages": 28},
  "items": [{"id": 1, "customer_id": 1, "...": "..."}]
}
```

### `GET /purchases/{id}` — single record

```bash
curl http://localhost:8000/purchases/42
```

Returns `404` when the id does not exist.

### `GET /search?q=...` — basic free-text search

Matches against `item_purchased`, `category`, `color`, `location`
(case-insensitive). Same pagination meta as `/purchases`.

```bash
curl "http://localhost:8000/search?q=sneakers"
```

### `GET /categories` — distinct categories

```bash
curl http://localhost:8000/categories
# ["Accessories","Clothing","Footwear","Outerwear"]
```

### `GET /stats` — aggregate stats

```bash
curl http://localhost:8000/stats
```

Returns totals, averages, and a per-category breakdown.

## Validation & error handling

- All numeric query params are range-checked by FastAPI / Pydantic
  (`page >= 1`, `0 <= min_rating <= 5`, etc.); violations return `422`.
- `min_amount > max_amount` returns `400` with an explanatory message.
- Unknown ids return `404`.
- Importer coerces malformed numeric cells to safe defaults rather
  than crashing the import.

## Known limitations / future improvements

- **Dataset access** — the real Drive CSV was not reachable from the
  sandbox; the generated sample is structurally faithful but synthetic.
  Replace `data/shopping.csv` with the real file and rerun the importer.
- **Read-only** — no `POST` / `PUT` / `DELETE` endpoints.
- **No auth** — the API is open; production deployments should add at
  least an API key middleware.
- **No rate limiting** — fine for local use, not for public exposure.
- **SQLite only** — works out of the box but doesn't scale to large
  concurrent workloads; a Postgres profile would be a natural next step.
- **Search is `ILIKE`-based** — fine for the dataset size, but a
  proper FTS5 index (or external search engine) would scale better.
- **No structured logging / metrics** — would be needed before
  shipping.

See the open GitHub issues on this repo for tracked follow-ups.
