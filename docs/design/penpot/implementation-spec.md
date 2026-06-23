# Customer Directory — First Page · Developer Handoff

**Stakeholder: Grace**
**Related app branch:** [`task002/shopping-api-dataset3`](https://github.com/ManuDiasCruz/ai-training-workspace-may/tree/task002/shopping-api-dataset3)
**Penpot prototype (view-only, no login required):**
<https://design.penpot.app/#/view/e35751e0-8829-45c8-a191-ab5fcd6565ff?page-id=f0485fb1-4e63-8165-8008-38abbef6c0a5&share-id=f0485fb1-4e63-8165-8008-38acfc2c729a&index=0>

This spec maps the prototype's first page to the existing **Shopping Customers API**
(FastAPI) so the frontend can be built without any backend changes. Only the
**first page** (the Customer Directory) is in scope for this sprint.

![Prototype preview](preview.png)

---

## 1. Scope

A single screen — the **Customer Directory** — which is the app's landing page.
It combines three things developers can wire directly to the API:

1. A KPI summary strip (from `GET /stats`).
2. A filter/sort toolbar (the query params of `GET /customers`).
3. A paginated, sortable customer table (the `items` of `GET /customers`).

Nothing on the page requires an endpoint that does not already exist.

## 2. Layout / regions

| Region | Position | Notes |
|--------|----------|-------|
| Sidebar | fixed left, 248 px | Brand, primary nav (Customers active), stakeholder card. Decorative for page 1 — only **Customers** routes here. |
| Top bar | 80 px, sticky | Page title, search input, **+ Add Customer** primary button. |
| KPI cards | 4-up grid | Bound to `GET /stats`. |
| Filter toolbar | full width card | Bound to `GET /customers` query params. |
| Table card | fills remaining height | Header row + 10 data rows + pagination footer. |

Canvas is `1440 × 1104`. Content area is fluid; the table and toolbar should
stretch with the viewport, the sidebar stays fixed-width. Use the
[`design-tokens.json`](design-tokens.json) in this folder for exact colors,
type scale, radii and spacing.

## 3. Data binding — API mapping

### 3.1 KPI cards → `GET /stats`

```json
{ "total_customers": 200, "by_gender": {"Female":112,"Male":88},
  "avg_age": 38.85, "avg_annual_income_k": 60.56, "avg_spending_score": 50.2 }
```

| Card | Field | Format |
|------|-------|--------|
| Total Customers | `total_customers` | integer |
| Avg. Age | `avg_age` | `38.85 years` |
| Avg. Annual Income | `avg_annual_income_k` | `$60.56k` (value is already in **k$**) |
| Avg. Spending Score | `avg_spending_score` | `50.2 / 100` |

The gender split bar above the table also comes from `by_gender`
(Female = rose, Male = blue), with percentages of `total_customers`.

### 3.2 Filter toolbar → `GET /customers` query params

| Control | Param(s) | Allowed values |
|---------|----------|----------------|
| Gender | `gender` | `Male` \| `Female` (omit = All) |
| Age | `min_age`, `max_age` | `0–130` |
| Income | `min_income`, `max_income` | `>= 0` (k$) |
| Spending | `min_score`, `max_score` | `1–100` |
| Search box (top bar) | `search` | case-insensitive substring of `customer_code` or `gender` |
| Sort | `sort_by` | `id` \| `age` \| `annual_income_k` \| `spending_score` \| `customer_code` |
| Desc/Asc toggle | `order` | `asc` (default) \| `desc` |
| Pagination | `page`, `page_size` | `page>=1`, `page_size 1–200` (design uses 10) |

> The API returns **HTTP 400** when a range is inverted (e.g. `min_age > max_age`).
> Surface this inline on the offending filter rather than as a global error.

### 3.3 Table rows → `GET /customers` → `items[]`

```json
{ "total": 200, "page": 1, "page_size": 10, "items": [
  { "id": 1, "customer_code": "0001", "gender": "Male",
    "age": 19, "annual_income_k": 15, "spending_score": 39 }
]}
```

| Column | Field | Rendering |
|--------|-------|-----------|
| # | `id` | muted surrogate id |
| Customer Code | `customer_code` | 600-weight, primary text |
| Gender | `gender` | pill badge (Female = rose, Male = blue) |
| Age | `age` | plain integer |
| Annual Income | `annual_income_k` | `$<n>k` |
| Spending Score | `spending_score` | progress bar (width = `score%`) + value, **color-banded** |
| Actions | — | **View** → `GET /customers/{id}`; **Delete** → `DELETE /customers/{id}` |

**Spending-score color bands** (see tokens): `1–33` amber `#D97706`,
`34–66` indigo `#4F46E5`, `67–100` green `#16A34A`.

Pagination footer: `Showing {(page-1)*page_size + 1}–{min(page*page_size,total)} of {total}`.

## 4. Actions & write paths

| UI | Endpoint | Notes |
|----|----------|-------|
| **+ Add Customer** | `POST /customers` | Body: `customer_code`, `gender`, `age`, `annual_income_k`, `spending_score`. Handle **409** (duplicate `customer_code`) and **422** (validation). |
| **View** (row) | `GET /customers/{id}` | Detail drawer/modal (not designed in page 1). Handle **404**. |
| **Delete** (row) | `DELETE /customers/{id}` | Confirm first; **204** on success, **404** if gone. |

## 5. States to implement (not all drawn — build them)

- **Loading:** skeleton rows in the table, shimmer on KPI values.
- **Empty:** filters return `total = 0` → empty-state inside the table card.
- **Error:** non-2xx from `/customers` or `/stats` → inline retry banner.
- **Validation (400):** inverted range filters — highlight the control.
- Search/filter changes should reset `page` to 1.

## 6. Build notes

- Suggested stack: any SPA framework; the layout is plain fl/grid + a table.
  Source Sans Pro (or system fallback) matches the prototype.
- All numbers in the prototype are **real sample data** from
  `data/Shopping_data.csv` (first 10 rows) so visual QA can diff against the API.
- Keep `annual_income_k` semantics explicit (**thousands of dollars**) in the UI.
- This is page **1 of the app**; nav items other than *Customers* are
  placeholders and out of scope for this sprint.
