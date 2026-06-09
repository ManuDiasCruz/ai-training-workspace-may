# Shopping Customers API - First Page Penpot Spec

Stakeholder: Mary

Related application branch: `task002/shopping-api-dataset3`

Design branch: `codex-prototype-penpot`

Scope: first page only. The page is a desktop-first customer analytics
dashboard at 1440 px reference width with a 1280 px content column.

## Goal

Create a frontend entry point for the existing API so an analyst can:

- confirm API health;
- read dataset summary metrics;
- browse, search, filter and sort customers;
- add a customer;
- delete a customer.

No new backend endpoints are required.

## Layout

1. Top bar
   - Left: `Shopping Customers`.
   - Right: API health badge and primary `New customer` button.
2. KPI row
   - Four cards: total customers, average age, average annual income and
     average spending score.
   - Total card includes the female and male counts.
3. Customers panel
   - Header with result count.
   - Toolbar: search input, gender filter, age range, income range, score
     range, sort field and sort order.
   - Table columns: code, gender, age, annual income, spending score and
     actions.
   - Pagination footer.

## API Mapping

| UI element | Endpoint | Implementation notes |
| --- | --- | --- |
| API health badge | `GET /health` | Green when `status == "ok"`; danger state on network failure. |
| KPI cards | `GET /stats` | Use `total_customers`, `by_gender`, `avg_age`, `avg_annual_income_k`, `avg_spending_score`. |
| Search | `GET /customers?search=` | Debounce 300 ms. Query length is 1 to 64 characters. |
| Gender filter | `GET /customers?gender=Male|Female` | Include an all-genders default that omits the parameter. |
| Age filter | `min_age`, `max_age` | Client validates `min <= max`; server may return 400. |
| Income filter | `min_income`, `max_income` | Client validates `min <= max`; values are in thousands. |
| Score filter | `min_score`, `max_score` | Valid domain is 1 to 100. |
| Sort control | `sort_by`, `order` | Supported fields: `id`, `age`, `annual_income_k`, `spending_score`, `customer_code`. |
| Table rows | `GET /customers` | Render `items[]`; keep query state in the URL. |
| New customer | `POST /customers` | Inline validation for `customer_code`, `gender`, `age`, `annual_income_k`, `spending_score`. |
| Delete row | `DELETE /customers/{id}` | Confirm first; optimistic remove with rollback on error. |

## States

- Loading: skeleton KPI cards and five skeleton table rows.
- Empty: "No customers match these filters" with a clear-filters action.
- Error: inline banner with retry. For 400, 409 and 422, place field-level
  messages next to the affected control.
- Loaded: table and KPI values populated from the API.

## Tokens

Use [design-tokens.json](./design-tokens.json) as the source of truth.

- Brand primary: `#4F46E5`.
- Canvas: `#F8FAFC`.
- Surface: `#FFFFFF`.
- Border: `#E2E8F0`.
- Primary text: `#0F172A`.
- Secondary text: `#475569`.
- Female accent: `#DB2777`.
- Male accent: `#2563EB`.
- Success: `#16A34A`.
- Warning: `#D97706`.
- Danger: `#DC2626`.
- Typeface: Inter.
- Control height: 40 px.
- Card radius: 12 px.
- Control radius: 8 px.
- Page padding: 32 px.

## Responsive Rules

- At 980 px and below, KPI cards wrap to two columns.
- At 768 px and below, page padding drops to 16 px, filters collapse into a
  drawer or stacked controls, and the table scrolls horizontally.
- Do not hide table columns by default; this is an analytics surface where field
  comparison matters.

## Accessibility

- Table uses real `th` cells and sortable headers expose `aria-sort`.
- All controls are keyboard reachable with a visible 2 px brand focus ring.
- Color is never the only status signal; score and gender chips include text.
- Destructive delete action needs accessible confirmation copy.

## Customization From Starting Template

The Penpot Hub Sales dashboard example is used only for dashboard structure
inspiration. This design is customized for the Shopping Customers API by:

- replacing sales KPIs with dataset statistics;
- replacing generic sales rows with real `CustomerOut` fields;
- adding API health, create-customer and delete-customer flows;
- adding gender chips and spending-score meters;
- mapping each toolbar control to an actual FastAPI query parameter;
- defining loading, empty, error and loaded states for implementation.
