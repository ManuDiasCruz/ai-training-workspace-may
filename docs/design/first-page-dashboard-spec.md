# Shopping Customers API — First Page Design Spec

**Stakeholder: Mary**

- **Related branch:** `task002/shopping-api-dataset3`
- **Design assets branch:** `design/shopping-dashboard-first-page`
- **Figma reference:** https://www.figma.com/design/oKTrOkpJPU0gW6qZvr2HC1
- **Scope:** First page only — the **Customer Analytics Dashboard**.

> **Figma status:** the Figma file above is the canonical design container for
> this work. The visual frames are pending population in Figma — the build was
> blocked by the workspace's Figma plan tool-call limit (Starter / View seat =
> 6 MCP calls per month). This document is the authoritative, developer-ready
> specification in the meantime: every token, layout and component below is
> exact and implementable as-is, and will be mirrored 1:1 into the Figma file
> once write access is restored.

---

## 1. Goal

The repository today is an **API-only** project that exposes the Mall Customer
Segmentation dataset through FastAPI. This design turns it into a
developer-ready **customer analytics dashboard** — a single first page that lets
an internal analyst browse, filter, search, inspect, create and delete customer
records, all backed by the endpoints that already exist.

No new backend endpoints are required. Every UI element below maps onto an
existing route documented in the root `README.md`.

## 2. Page: Customer Analytics Dashboard

Desktop-first, 1440 px reference width, 1280 px content column, responsive down
to 768 px (filters collapse into a drawer; table becomes horizontally
scrollable).

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Shopping Customers            [● API: healthy]        [ + New customer ]   │  ← Top bar
├──────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ Total    │  │ Avg age  │  │ Avg income│ │ Avg score │                   │  ← KPI cards (/stats)
│  │  200     │  │  38.9    │  │  60.6 k$  │ │  50.2     │                    │
│  │ ♀112 ♂88 │  │  years   │  │  annual   │ │  1–100    │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
├──────────────────────────────────────────────────────────────────────────┤
│  Customers                                                   200 results     │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ [🔍 Search code or gender]  [Gender ▾] [Age ▾] [Income ▾] [Score ▾]  │   │  ← Toolbar (/customers params)
│  │                                          [Sort by ▾]  [asc/desc ⇅]    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Code   │ Gender │ Age │ Income (k$) │ Spending score │       Actions  │   │  ← Table header
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │ 0001   │ ♂ Male │ 19  │ 15          │ ▓▓░░ 39        │       🗑 Delete │   │  ← rows (items[])
│  │ 0002   │ ♂ Male │ 21  │ 15          │ ▓▓▓▓ 81        │       🗑 Delete │   │
│  │ …                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  Showing 1–20 of 200                          ‹ Prev   1 2 3 … 10   Next ›   │  ← Pagination
└──────────────────────────────────────────────────────────────────────────┘
```

## 3. Design tokens

These are the canonical tokens. They are also seeded as a Figma variable
collection named **"Shopping Dashboard Tokens"** in the reference file.

### Color

| Token                       | Hex       | Usage                                  |
|-----------------------------|-----------|----------------------------------------|
| `color/brand/primary`       | `#4F46E5` | Primary buttons, active controls, links|
| `color/brand/primary-hover` | `#4338CA` | Primary button hover/pressed           |
| `color/brand/tint`          | `#EEF2FF` | Active filter pill background, focus    |
| `color/bg/canvas`           | `#F8FAFC` | Page background                        |
| `color/bg/surface`          | `#FFFFFF` | Cards, table, toolbar surfaces         |
| `color/bg/subtle`           | `#F1F5F9` | Table header row, zebra rows           |
| `color/border/default`      | `#E2E8F0` | Card / table / input borders           |
| `color/text/primary`        | `#0F172A` | Headings, values                       |
| `color/text/secondary`      | `#475569` | Body text, labels                      |
| `color/text/muted`          | `#94A3B8` | Captions, placeholders                 |
| `color/accent/female`       | `#DB2777` | Female gender chip                     |
| `color/accent/male`         | `#2563EB` | Male gender chip                       |
| `color/status/success`      | `#16A34A` | Healthy API badge, high score          |
| `color/status/success-bg`   | `#DCFCE7` | High spending-score chip background    |
| `color/status/warn-bg`      | `#FEF3C7` | Mid spending-score chip background     |
| `color/status/warn-text`    | `#92400E` | Mid spending-score chip text           |
| `color/status/danger`       | `#DC2626` | Delete action, destructive states      |
| `color/status/danger-bg`    | `#FEE2E2` | Low spending-score chip background     |

### Type — Inter

| Role         | Size / line-height | Weight     |
|--------------|--------------------|------------|
| Display / KPI value | 28 / 36     | Semi Bold  |
| H1 page title| 20 / 28            | Semi Bold  |
| Section title| 16 / 24            | Semi Bold  |
| Body         | 14 / 20            | Regular    |
| Label / table head | 13 / 18      | Medium     |
| Caption      | 12 / 16            | Regular    |

### Spacing, radius, elevation

- Spacing scale (px): `4, 8, 12, 16, 24, 32`. Page padding `32`, card padding `20`, control height `40`.
- Radius: inputs/buttons `8`, cards `12`, chips/pills `999` (full).
- Elevation: cards use a single soft shadow `0 1px 2px rgba(15,23,42,0.06)` plus the `border/default` 1px border.

## 4. Components mapped to the API

| UI element              | Endpoint / contract                                   | Notes |
|-------------------------|-------------------------------------------------------|-------|
| API health badge        | `GET /health` → `{status:"ok"}`                       | Green dot when ok; red when unreachable. |
| KPI: Total customers    | `GET /stats` → `total_customers`                      | Sub-line shows `by_gender` split (`♀ Female / ♂ Male`). |
| KPI: Avg age            | `GET /stats` → `avg_age`                              | 1 decimal, suffix "years". |
| KPI: Avg annual income  | `GET /stats` → `avg_annual_income_k`                  | 1 decimal, suffix "k$". |
| KPI: Avg spending score | `GET /stats` → `avg_spending_score`                   | 1 decimal, scale "1–100". |
| Search box              | `GET /customers?search=` (min 1, max 64 chars)        | Case-insensitive match on `customer_code` + `gender`. Debounce 300 ms. |
| Gender filter           | `?gender=Male|Female`                                 | Tri-state: All / Male / Female. |
| Age filter              | `?min_age=&max_age=` (0–130)                          | Dual range; client guard `min ≤ max` (server returns 400 otherwise). |
| Income filter           | `?min_income=&max_income=` (≥ 0)                      | Same min ≤ max guard. |
| Score filter            | `?min_score=&max_score=` (1–100)                      | Same min ≤ max guard. |
| Sort control            | `?sort_by=&order=`                                    | `sort_by ∈ {id, age, annual_income_k, spending_score, customer_code}`, `order ∈ {asc, desc}`. |
| Customer table rows     | `GET /customers` → `items[]` of `CustomerOut`         | Columns: `customer_code`, `gender`, `age`, `annual_income_k`, `spending_score`, actions. |
| Spending-score chip     | derived from `spending_score`                         | 1–33 danger-bg, 34–66 warn-bg, 67–100 success-bg. |
| Row delete              | `DELETE /customers/{id}` → 204; 404 if missing        | Confirm dialog; optimistic removal + rollback on error. |
| New customer button+form| `POST /customers` → 201 `CustomerOut`; 409 duplicate  | Fields = `CustomerCreate`: `customer_code` (1–8), `gender` (Male/Female), `age` (0–130), `annual_income_k` (≥0), `spending_score` (1–100). |
| Pagination              | `?page=&page_size=` + response `total,page,page_size` | `page ≥ 1`, `page_size` 1–200 (default 20). Footer: "Showing X–Y of total". |

## 5. States

Every data region must implement four states:

- **Loading:** skeleton rows in the table; shimmer placeholders in KPI cards.
- **Empty:** table shows "No customers match these filters" with a "Clear filters" action.
- **Error:** inline banner with the API `detail` string and a "Retry" button. For `422`/`400`, surface the field-level message next to the offending control — never a browser `alert()`.
- **Loaded:** the layout above.

## 6. Interaction notes (developer-facing)

- **Keep all filter/sort/search/pagination state in the URL query string**, using
  the exact parameter names above, so views are shareable and back/forward work.
- **Validate ranges client-side** (`min_age ≤ max_age`, etc.) to avoid a
  round-trip `400`, but still handle the `400` defensively.
- **Create-customer validation is inline** (per-field), mirroring the Pydantic
  constraints; map a `409` to a "customer code already exists" message on the
  `customer_code` field.
- **Delete** uses a confirmation step and optimistic UI with rollback on failure.

## 7. Accessibility

- Color is never the only signal: gender and spending-score chips include text
  labels/values, not just background color.
- All interactive controls reachable by keyboard; visible focus ring uses
  `color/brand/primary` at 2px.
- Table uses real `<th>` headers with `scope`; sortable columns expose
  `aria-sort`.
- Target contrast AA: `text/secondary` on `bg/surface` and chip text on chip
  backgrounds all meet ≥ 4.5:1.

## 8. Handoff / next steps

1. Populate the Figma file (`oKTrOkpJPU0gW6qZvr2HC1`) with the frames described
   here once Figma write access is available (Full/Dev seat or refreshed quota).
2. Implement the page against the existing API — see the linked GitHub issue for
   the developer task breakdown.
3. This is **page one only**; customer-detail and create-as-page flows are
   out of scope for this iteration.
