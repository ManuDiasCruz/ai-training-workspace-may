# Shopping Customers API — First Page Design Spec (Penpot)

**Stakeholder: Mary**

- **Related app branch:** `task002/shopping-api-dataset3`
- **Design assets branch:** `design/shopping-first-page-penpot`
- **Design tool:** [Penpot](https://penpot.app) (open-source, self-hostable design & prototyping platform)
- **Starting template:** [Penpot Hub → "Sales dashboard example"](https://penpot.app/penpothub/libraries-templates/sales-dashboard-example)
  (free community template). Layout grid, card and table primitives were reused
  and then **meaningfully customized** for this project — see §9.
- **Token source of truth:** [`design-tokens.json`](./design-tokens.json) — W3C
  DTCG format, importable into Penpot via **Tokens → Import**.
- **Renderable reference:** [`prototype/index.html`](./prototype/index.html) — open
  in any browser; pixel-faithful to the Penpot frame and wired 1:1 to the tokens.
- **Scope:** First page only — the **Customer Analytics Dashboard**.

> **Why Penpot, and what "developer-ready" means here.** The app today is an
> API-only FastAPI project. This reference turns it into a single, implementable
> dashboard page. Every token, layout measurement, component and state below is
> exact. The accompanying `prototype/` is a runnable HTML/CSS rendering of the
> Penpot frame so a developer can inspect spacing, color and behavior directly,
> and `design-tokens.json` drops straight into Penpot (or a CSS/Tailwind/Style
> Dictionary pipeline) without re-keying values.

---

## 1. Goal

Give an internal analyst one page to **browse, filter, search, inspect, create
and delete** customer records from the Mall Customer Segmentation dataset,
backed entirely by endpoints that already exist. **No new backend endpoints are
required.**

## 2. Page: Customer Analytics Dashboard

Desktop-first, **1440 px** reference width, **1280 px** content column,
responsive down to **768 px** (filters collapse into a drawer; table scrolls
horizontally).

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Shopping Customers            [● API: healthy]        [ ＋ New customer ]   │  ← Top bar
├──────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ Total    │  │ Avg age  │  │ Avg income│ │ Avg score │                   │  ← KPI cards (/stats)
│  │  200     │  │  38.9    │  │  60.6 k$  │ │  50.2     │                    │
│  │ ♀112 ♂88 │  │  years   │  │  per cust.│ │  1–100    │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
├──────────────────────────────────────────────────────────────────────────┤
│  Customers                                                   200 results     │
│  [🔍 Search code or gender]  [Gender ▾] [Age ▾] [Income ▾] [Score ▾]        │  ← Toolbar (/customers params)
│                                              [Sort by ▾]  [asc/desc ⇅]       │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Code │ Gender │ Age │ Income (k$) │ Spending score │        Actions   │   │  ← Table header
│  │ 0001 │ ♂ Male │ 19  │ 15          │ ▓▓░░ 39        │        🗑 Delete  │   │  ← rows (items[])
│  │ 0002 │ ♂ Male │ 21  │ 15          │ ▓▓▓▓ 81        │        🗑 Delete  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  Showing 1–20 of 200                          ‹ Prev   1 2 3 … 10   Next ›   │  ← Pagination
└──────────────────────────────────────────────────────────────────────────┘
```

## 3. Design tokens

Canonical values live in [`design-tokens.json`](./design-tokens.json). Import as
a Penpot token set named **"Shopping Dashboard Tokens"**. Summary:

### Color
| Token | Hex | Usage |
|---|---|---|
| `color.brand.primary` | `#4F46E5` | Primary buttons, active controls, links |
| `color.brand.primary-hover` | `#4338CA` | Primary hover/pressed |
| `color.brand.tint` | `#EEF2FF` | Active filter pill bg, focus, row hover |
| `color.bg.canvas` | `#F8FAFC` | Page background |
| `color.bg.surface` | `#FFFFFF` | Cards, table, toolbar |
| `color.bg.subtle` | `#F1F5F9` | Table header, zebra rows |
| `color.border.default` | `#E2E8F0` | Card / table / input borders |
| `color.text.primary` | `#0F172A` | Headings, values |
| `color.text.secondary` | `#475569` | Body text, labels |
| `color.text.muted` | `#94A3B8` | Captions, placeholders |
| `color.accent.female` | `#DB2777` | Female gender chip |
| `color.accent.male` | `#2563EB` | Male gender chip |
| `color.status.success` / `success-bg` | `#16A34A` / `#DCFCE7` | Healthy badge, high score |
| `color.status.warn-bg` / `warn-text` | `#FEF3C7` / `#92400E` | Mid score chip |
| `color.status.danger` / `danger-bg` | `#DC2626` / `#FEE2E2` | Delete, low score |

### Type — Inter
| Role | Size / line-height | Weight |
|---|---|---|
| Display / KPI value | 28 / 36 | 600 |
| H1 page title | 20 / 28 | 600 |
| Section title | 16 / 24 | 600 |
| Body | 14 / 20 | 400 |
| Label / table head | 13 / 18 | 500 |
| Caption | 12 / 16 | 400 |

### Spacing, radius, elevation
- Spacing scale (px): `4, 8, 12, 16, 24, 32`. Page padding `32`, card padding `20`, control height `40`.
- Radius: inputs/buttons `8`, cards `12`, chips/pills `999` (full).
- Elevation: cards use `0 1px 2px rgba(15,23,42,0.06)` + 1px `border.default`.

## 4. Components mapped to the API

| UI element | Endpoint / contract | Notes |
|---|---|---|
| API health badge | `GET /health` → `{status:"ok"}` | Green dot when ok; red when unreachable. |
| KPI: Total customers | `GET /stats` → `total_customers` | Sub-line shows `by_gender` split (`♀ Female / ♂ Male`). |
| KPI: Avg age | `GET /stats` → `avg_age` | 1 decimal, suffix "years". |
| KPI: Avg annual income | `GET /stats` → `avg_annual_income_k` | 1 decimal, suffix "k$". |
| KPI: Avg spending score | `GET /stats` → `avg_spending_score` | 1 decimal, scale "1–100". |
| Search box | `GET /customers?search=` (1–64 chars) | Case-insensitive match on `customer_code` + `gender`. Debounce 300 ms. |
| Gender filter | `?gender=Male\|Female` | Tri-state: All / Male / Female. |
| Age filter | `?min_age=&max_age=` (0–130) | Dual range; client guard `min ≤ max` (server returns 400 otherwise). |
| Income filter | `?min_income=&max_income=` (≥ 0) | Same `min ≤ max` guard. |
| Score filter | `?min_score=&max_score=` (1–100) | Same `min ≤ max` guard. |
| Sort control | `?sort_by=&order=` | `sort_by ∈ {id, age, annual_income_k, spending_score, customer_code}`, `order ∈ {asc, desc}`. |
| Customer table rows | `GET /customers` → `items[]` of `CustomerOut` | Columns: `customer_code`, `gender`, `age`, `annual_income_k`, `spending_score`, actions. |
| Spending-score chip/bar | derived from `spending_score` | 1–33 danger, 34–66 warn, 67–100 success. |
| Row delete | `DELETE /customers/{id}` → 204; 404 if missing | Confirm dialog; optimistic removal + rollback on error. |
| New customer button + form | `POST /customers` → 201 `CustomerOut`; 409 duplicate | Fields = `CustomerCreate`: `customer_code` (1–8), `gender` (Male/Female), `age` (0–130), `annual_income_k` (≥0), `spending_score` (1–100). |
| Pagination | `?page=&page_size=` + response `total,page,page_size` | `page ≥ 1`, `page_size` 1–200 (default 20). Footer: "Showing X–Y of total". |

## 5. States

Every data region implements four states:
- **Loading:** skeleton rows in the table; shimmer placeholders in KPI cards.
- **Empty:** "No customers match these filters" + a "Clear filters" action.
- **Error:** inline banner with the API `detail` string and a "Retry" button.
  For `422`/`400`, surface the field-level message next to the offending control —
  never a browser `alert()`.
- **Loaded:** the layout in §2.

## 6. Interaction notes (developer-facing)

- **Keep all filter/sort/search/pagination state in the URL query string**, using
  the exact parameter names in §4, so views are shareable and back/forward work.
- **Validate ranges client-side** (`min_age ≤ max_age`, etc.) to avoid a
  round-trip `400`, but still handle the `400` defensively.
- **Create-customer validation is inline** (per-field), mirroring the Pydantic
  constraints; map a `409` to "customer code already exists" on the
  `customer_code` field.
- **Delete** uses a confirmation step and optimistic UI with rollback on failure.

## 7. Accessibility

- Color is never the only signal: gender and spending-score chips include text
  labels/values, not just background color.
- All interactive controls reachable by keyboard; visible focus ring uses
  `color.brand.primary` at 2px.
- Table uses real `<th>` headers with `scope`; sortable columns expose `aria-sort`.
- Target contrast AA: `text.secondary` on `bg.surface` and chip text on chip
  backgrounds all meet ≥ 4.5:1.

## 8. Working with this design in Penpot

1. Create a Penpot project **"Shopping Customers — Dashboard"** and a page
   **"01 · Customer Analytics Dashboard"**.
2. **Tokens → Import** → select [`design-tokens.json`](./design-tokens.json).
   This seeds the color, typography, spacing, radius and shadow sets.
3. (Optional) Import the [Sales dashboard example](https://penpot.app/penpothub/libraries-templates/sales-dashboard-example)
   as a shared library to reuse its card/table primitives, then re-skin them with
   the imported tokens (see §9 for what changed).
4. Build the frame at 1440 px following §2; use the [`prototype/`](./prototype/)
   rendering as the visual ground truth for spacing and color.
5. Export frames as PNG/SVG into this folder for the developer handoff if needed.

## 9. Customization vs. the starting template

The Penpot "Sales dashboard example" was used only as a structural starting
point. It was adapted for this project as follows:

- **Information model** rebuilt around the actual API: KPI cards bind to
  `GET /stats`; the data table columns are the real `CustomerOut` fields, not the
  template's sales rows.
- **Token system replaced** with the indigo/slate palette + Inter scale in
  [`design-tokens.json`](./design-tokens.json) (the template ships its own colors).
- **Domain components added** that the template lacks: tri-state gender chips,
  the 3-band spending-score meter, the API-health badge, and a create-customer
  entry point mapped to `POST /customers`.
- **Filtering/sorting/pagination toolbar** redesigned to match the exact query
  parameters the FastAPI service accepts (the template has none of these).
- **Four explicit data states** (loading / empty / error / loaded) specified for
  every region — the template only shows a populated state.

## 10. Handoff / next steps

1. Implement the page against the existing API — see the linked GitHub issue for
   the developer task breakdown.
2. This is **page one only**; customer-detail and create-as-page flows are out of
   scope for this iteration.
3. If a hosted Penpot file is provisioned, import `design-tokens.json` and lay
   out the §2 frame; this spec + `prototype/` remain the source of truth in the
   meantime.
