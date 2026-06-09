# Shopping Customers - First Page Specification

Stakeholder: Mary

Related application branch: `task002/shopping-api-dataset3`

Design branch: `kindle-aplha-prototype-penpot`

## Product Goal

Give an analyst one efficient surface to confirm service health, understand the
dataset at a glance, find customer records, compare values, add a record and
remove a record. Scope is limited to this first page.

## Frame And Layout

- Desktop reference: 1440 x 1024 px, content max-width 1360 px.
- Header: product identity, endpoint health and primary create action.
- KPI band: total customers, average age, average annual income and average
  spending score from the current 200-row dataset.
- Directory toolbar: search, filter disclosure, active filter chips, sorting and
  result count.
- Customer table: code, gender, age, annual income, spending score and actions.
- Pagination remains attached to the table so the record context is preserved.

## API Mapping

| UI | Endpoint or field | Behavior |
| --- | --- | --- |
| API status | `GET /health` | Healthy only when `status` is `ok`; network failure shows retry. |
| KPI band | `GET /stats` | Use all fields from `StatsOut`; format averages to one decimal. |
| Search | `GET /customers?search=` | Debounce 300 ms; omit an empty query. |
| Gender | `gender` | `Male`, `Female`, or omit for all. |
| Age | `min_age`, `max_age` | Validate 0-130 and `min <= max` before request. |
| Income | `min_income`, `max_income` | Values are thousands of dollars and must be non-negative. |
| Score | `min_score`, `max_score` | Validate 1-100 and `min <= max`. |
| Sort | `sort_by`, `order` | Supported fields are defined by `app/main.py`. |
| Table | `items[]` from `GET /customers` | Use `customer_code` as the visible record identifier. |
| Create | `POST /customers` | Drawer or modal; inline 409 and 422 feedback. |
| Delete | `DELETE /customers/{id}` | Confirmation includes customer code; restore row on failure. |
| Pagination | `page`, `page_size` | Keep all controls in the URL query string. |

## Component Contract

- Buttons use icons for create, filters, sort, pagination, close and delete.
- The primary action is the only solid brand button in the header.
- Filter chips are removable and summarize only active constraints.
- Spending score combines a numeric value and horizontal meter; thresholds are
  1-39 low, 40-69 medium and 70-100 high.
- Gender badges include text and use color only as secondary reinforcement.
- Row delete uses an icon button with an accessible label and tooltip.

## States

- Loading: preserve the table dimensions with six skeleton rows and metric
  placeholders.
- Empty: keep the toolbar visible, show "No customers match these filters" and
  provide a clear-filters action.
- Error: use an inline banner inside the affected region with a retry action.
- Create errors: map 422 details to fields; use a top-of-form message for 409.
- Delete: disable the row action while pending; restore on network failure.

## Responsive Behavior

- 980 px and below: KPI cards become two columns; toolbar actions wrap.
- 760 px and below: header actions remain visible, KPI cards become one column,
  filters move into a disclosure panel and the table scrolls horizontally.
- Keep all table columns. This surface is intended for record comparison.

## Accessibility

- Use semantic table headers and `aria-sort` for sortable columns.
- Maintain visible focus with a 2 px `#0F766E` outline and 2 px offset.
- Minimum control target is 40 x 40 px.
- Announce result counts and request errors with polite live regions.
- Delete confirmation names the exact customer code.

## Template Adaptation

The Penpot Hub Sales Dashboard example was used only for initial grid and card
proportions. This design replaces its sales domain with actual API fields and
values, adds the service health and record lifecycle, uses a quieter operational
palette, defines backend-aware errors and documents every query parameter.
