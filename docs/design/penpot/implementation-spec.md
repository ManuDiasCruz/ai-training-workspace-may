# Customer Overview — Implementation Spec (Frontend Handoff)

**Stakeholder: Cora**
**Design branch:** `O48-H-prototype-penpot` · **Reference app branch:** `task002/shopping-api-dataset3`
**Penpot prototype (public view link):** https://design.penpot.app/#/view?file-id=cf421b06-918b-81ac-8008-4bf96da5d669&page-id=cf421b06-918b-81ac-8008-4bf96da5d66a&section=interactions&index=0&share-id=279d72fe-2334-8043-8008-4bfe6fa40647
**Scope:** *First page only* — the **Customer Overview** dashboard. No new backend endpoints are required; the layout is mapped 1:1 to the existing FastAPI contract.

---

## 1. What this page is

A single-page analytics workspace for the **Shopping Customers API** (Mall Customer
Segmentation dataset — 200 customers). It surfaces the dataset's aggregate statistics,
a behavioural-segmentation view, and a filterable/sortable/paginated customer table.

Reference renders:
- Static canvas: [`../customer-segmentation-dashboard.svg`](../customer-segmentation-dashboard.svg)
- Runnable HTML: [`prototype/index.html`](prototype/index.html)
- Tokens: [`../design-tokens.json`](../design-tokens.json)

---

## 2. Layout regions → API mapping

| Region | UI element | API call | Response field |
|--------|-----------|----------|----------------|
| Top bar | "API healthy" pill | `GET /health` | `{"status":"ok"}` → green pill; anything else → red "API unavailable" |
| Top bar | Search box | `GET /customers?search=<q>` | debounced; `min_length=1, max_length=64` |
| Top bar | **+ New customer** | `POST /customers` | opens create form (see §5) |
| KPI row | Total Customers | `GET /stats` | `total_customers` |
| KPI row | Avg Age | `GET /stats` | `avg_age` |
| KPI row | Avg Annual Income | `GET /stats` | `avg_annual_income_k` (render as `$<n>k`) |
| KPI row | Avg Spending Score | `GET /stats` | `avg_spending_score` |
| Insight | Gender split donut | `GET /stats` | `by_gender` (e.g. `{"Female":112,"Male":88}`) |
| Insight | Segmentation scatter | `GET /customers?page_size=200` | plot `annual_income_k` (x) vs `spending_score` (y); colour by band |
| Table | Rows | `GET /customers` | `items[]` → `id, customer_code, gender, age, annual_income_k, spending_score` |
| Table | Result count | `GET /customers` | `total` |
| Footer | Pagination | `GET /customers?page=&page_size=` | `page`, `page_size`, `total` |

> The scatter can also be fed by one page at a time; for 200 rows a single
> `page_size=200` fetch is simplest and matches the API's `le=200` cap.

---

## 3. Filter bar → query parameters

All controls map directly to `GET /customers` query params. Types/limits are taken
from `app/main.py` so the client can validate before calling:

| Control | Param | Constraints |
|---------|-------|-------------|
| Gender (All / Female / Male) | `gender` | `^(Male\|Female)$` or omit for All |
| Age range | `min_age`, `max_age` | `0..130`; client blocks `min_age > max_age` (API returns **400**) |
| Income range | `min_income`, `max_income` | `>= 0`; `min_income > max_income` → **400** |
| Score range | `min_score`, `max_score` | `1..100`; `min_score > max_score` → **400** |
| Sort by | `sort_by` | one of `id \| age \| annual_income_k \| spending_score \| customer_code` |
| Order | `order` | `asc` (default) \| `desc` |
| Page size | `page_size` | `1..200` (default 20) |
| Page | `page` | `>= 1` |

Example the prototype represents (spending, high→low):
```
GET /customers?sort_by=spending_score&order=desc&page=1&page_size=20
```

---

## 4. Spending-score bands (client-side derivation)

The API returns a raw `spending_score` (1–100). The band chip + bar colour is a
**presentation-only** mapping — do not expect it from the backend:

| Band | Range | Dot / bar | Text |
|------|-------|-----------|------|
| Low  | 1–33  | `#F59E0B` | `#B45309` |
| Mid  | 34–66 | `#6366F1` | `#4338CA` |
| High | 67–100| `#16A34A` | `#166534` |

Bar width = `spending_score%`.

---

## 5. Create customer (POST /customers)

Form fields mirror `CustomerCreate`:

| Field | Input | Validation |
|-------|-------|-----------|
| `customer_code` | text | 1–8 chars, unique |
| `gender` | select | Male / Female |
| `age` | number | 0–130 |
| `annual_income_k` | number | ≥ 0 |
| `spending_score` | number | 1–100 |

Responses: **201** created → prepend row & refresh `/stats`; **409** duplicate
`customer_code` → inline error on the code field; **422** → field-level validation
errors from the Pydantic detail payload.

---

## 6. States to build

- **Loading** — skeleton rows for the table, shimmer on KPI values.
- **Empty** — filters return `total: 0` → "No customers match these filters" with a *Clear filters* action.
- **Validation (400)** — invalid range combination → toast + highlight the offending range control.
- **Not found (404)** — deep-linked customer id missing → inline empty state in the detail drawer.
- **API down** — `/health` fails → red pill "API unavailable" and a non-blocking banner.

---

## 7. Responsive behaviour

- `≥ 1100px` — 4 KPI columns, 2-column insight row, full sidebar (240px).
- `720–1100px` — KPI collapses to 2 columns; insight cards stack.
- `< 720px` — sidebar collapses to a top menu; table becomes horizontally scrollable
  (keep ID + Code + Score sticky where possible).

---

## 8. Component inventory (for a design system / code components)

`AppSidebar`, `TopBar`, `HealthPill`, `SearchInput`, `KpiCard`, `GenderDonut`,
`SegmentScatter`, `FilterBar` (+ `RangeControl`, `SelectControl`), `CustomerTable`
(+ `GenderTag`, `ScoreBand`), `Pager`, `NewCustomerButton`. Tokens for all of these
live in [`../design-tokens.json`](../design-tokens.json).

---

*This spec is intentionally limited to the first page requested for this sprint.
It maps only to endpoints that exist today in `task002/shopping-api-dataset3`; no
speculative backend work is implied.*
