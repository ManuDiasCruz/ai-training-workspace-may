# Customer intelligence dashboard — design specification

Stakeholder: Lisa

This specification accompanies the Penpot-importable first-page source in
[`shopping-customers-dashboard.svg`](./shopping-customers-dashboard.svg).
Import the SVG into a 1440 × 1024 Penpot board; its groups, text, shapes, and
paths remain editable.

## Product direction

The first page turns the existing Shopping Customers API into an operations
dashboard. It leads with the decisions the dataset can support—audience size,
income, spending, and gender mix—then provides direct access to the customer
records. The visual language is calm, compact, and data-first rather than a
generic e-commerce storefront.

## Layout and responsive behaviour

- **Desktop (≥ 1200 px):** 232 px persistent sidebar, 40 px page gutters,
  four KPI cards, two-column insights, and the full six-column table.
- **Tablet (768–1199 px):** sidebar collapses to a 72 px rail; KPI cards use a
  2 × 2 grid; the insights cards stack; the table remains horizontally
  scrollable with Customer pinned.
- **Mobile (< 768 px):** navigation becomes a bottom bar; KPI cards and insight
  cards stack; customer records become summary cards. Search remains sticky;
  filters open in a bottom sheet.
- Keep the primary content width fluid and cap it at 1,280 px. Use an 8 px
  spacing grid and 44 px minimum interactive targets.

## Design tokens

| Token | Value | Use |
|---|---:|---|
| `color.brand.600` | `#6D5DFB` | Primary actions, active states, chart line |
| `color.brand.700` | `#4B3FCE` | Primary-action gradient end |
| `color.navy.900` | `#101A36` | Sidebar |
| `color.ink.900` | `#16213E` | Headings and metrics |
| `color.ink.600` | `#68738B` | Body text |
| `color.surface` | `#FFFFFF` | Cards and top bar |
| `color.canvas` | `#F6F7FB` | Page background |
| `color.line` | `#E6E9F1` | Dividers and control borders |
| `color.success` | `#168E6A` | Healthy API and positive states |
| `radius.control` | `12 px` | Inputs and buttons |
| `radius.card` | `18 px` | Dashboard cards |
| `shadow.card` | `0 8px 28px rgba(16,32,68,.08)` | Card elevation |

Typography: Inter where available, then system UI. Page heading is 30/36,
section heading 18/24, body 14/20, table header 11/16 uppercase. Body text and
interactive controls must maintain WCAG AA contrast.

## API-to-UI contract

| UI region | Endpoint / parameter | Rendering rule |
|---|---|---|
| KPI cards | `GET /stats` | Use `total_customers`, `avg_annual_income_k`, `avg_spending_score`, and `by_gender` |
| Gender mix | `GET /stats` | Convert counts in `by_gender` to percentages using `total_customers` |
| Customer table | `GET /customers` | Use `customer_code`, `gender`, `age`, `annual_income_k`, and `spending_score` |
| Search | `/customers?search=` | Debounce 300 ms; reset `page=1` when the query changes |
| Filters | `/customers?gender=&min_age=&max_age=&min_income=&max_income=&min_score=&max_score=` | Apply explicitly; show an active-filter count; preserve filters in the URL |
| Sort | `/customers?sort_by=&order=` | Default to `sort_by=id&order=asc`; expose sortable table headers |
| Pagination | `/customers?page=&page_size=` | Default to 20; options 20, 50, 100; never exceed the API limit of 200 |
| Add customer | `POST /customers` | Open a modal; validate client-side to match the Pydantic schema |
| API status | `GET /health` | Green for `status=ok`; show a non-blocking degraded-state banner on failure |

The “Customer signals” visual in the prototype is a directional composition.
With the current API, bind the labelled Age, Income, and Spend values to the
three averages from `/stats`. A time-series chart requires a future aggregate
endpoint and should not be implied by implementation.

## Interaction and state notes

- Search, filters, sort, page, and page size are shareable URL state.
- Use skeletons that match final card and row geometry during loading.
- Empty state: “No customers match these filters” with actions to clear filters
  or add a customer.
- Error state: retain the last successful data when available and place a
  retry banner above the affected region.
- Spending score bars are semantic: 1–33 red, 34–66 amber, 67–100 green. Do
  not communicate score by colour alone; always display the number.
- Row overflow offers “View details” and “Delete”. Deletion requires a
  confirmation dialog that names the customer code.
- Keyboard order follows visual order. All icon-only actions require accessible
  names and visible focus indicators.

## Penpot handoff checklist

1. Import the SVG into Penpot and name the page `01 · Customer intelligence`.
2. Convert Sidebar, KPI card, Button, Input, Badge, Table row, and Pagination
   into components using the tokens above.
3. Add a prototype flow starting at this page. Link **Customers** to the future
   list page, **Add customer** to a modal overlay, and the API status item to a
   status panel when those screens are designed.
4. Preserve a 1440 px desktop board and add tablet/mobile boards using the
   responsive rules above.

