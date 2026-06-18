# Customer Intelligence — first-page implementation specification

Stakeholder: Mary

- Application source branch: `task002/shopping-api-dataset3`
- Design/handoff branch: `claude-prototype-penpot`
- Page scope: one authenticated-looking application shell is depicted, but auth
  itself is explicitly out of scope because the service does not expose it.
- Reference viewport: 1440 × 1024; content max-width 1280 px.

## Page contract

The first page is a responsive customer analytics workspace. On initial load it
requests `/health`, `/stats`, and `/customers?page=1&page_size=20`. Do not gate
customer results on the health response; each region handles failure locally.

| Region / control | API mapping and behavior |
| --- | --- |
| API health badge | `GET /health`; show `Online` for `{status: "ok"}`, `Offline` on failure. Refresh every 60 s while visible. |
| Total customers | `GET /stats` → `total_customers`; secondary line reads `by_gender.Female` and `.Male`. |
| Average age | `GET /stats` → `avg_age`, one decimal and suffix `years`. |
| Average income | `GET /stats` → `avg_annual_income_k`, one decimal and suffix `k$`. |
| Average score | `GET /stats` → `avg_spending_score`, one decimal and scale `of 100`. |
| Search | `/customers?search=`; matches code or gender; 300 ms debounce; 1–64 chars when present. |
| Gender | `gender=Male` or `Female`; All omits the parameter. |
| Age | `min_age`, `max_age` in 0–130; omit blank bounds. |
| Income | `min_income`, `max_income`, both ≥ 0. |
| Score | `min_score`, `max_score` in 1–100. |
| Sort | `sort_by` is `id`, `age`, `annual_income_k`, `spending_score`, or `customer_code`; `order` is `asc` or `desc`. |
| Paging | Use `page` and `page_size`; render totals from `total`, `page`, and `page_size` rather than assuming 200. |
| Data rows | Render `customer_code`, `gender`, `age`, `annual_income_k`, and `spending_score`. Keep `id` for actions and keys. |
| New customer | `POST /customers`; form fields exactly match `CustomerCreate`; add returned row or refetch page 1. |
| Delete | `DELETE /customers/{id}`; confirm with customer code, disable action in flight, optimistically remove and restore on error. |

All filter, search, sort, and paging state must live in the URL query string
using the server's exact parameter names. This makes analysis views shareable,
survives refresh, and preserves forward/back behavior.

## Structure and dimensions

- Page gutter: 32 px at ≥ 1024 px; 20 px at 768–1023 px; 16 px below 768 px.
- Header: 64 px navy bar, logo left; utility items right. The large greeting and
  page action live in a separate 128 px hero inside the content column.
- Metrics: four equal cards, 16 px gap, 20 px inner padding, 16 px radius.
- Customers panel: one white surface with 24 px heading/toolbar padding, 56 px
  table header, and 64 px data rows.
- Filters: the search control is 300 px minimum. Desktop keeps primary filters
  visible; under 768 px, show Search and a single `Filters (n)` button. Render
  remaining filters in a keyboard-dismissible sheet.
- Table: min-width 920 px and horizontal scrolling below that width. Keep Code
  and the row action column sticky on small desktops if feasible.

## Visual and component behavior

Use tokens from `design-tokens.json`; do not sample approximate colours from the
SVG. Text uses Inter with system fallbacks. Body copy is 14/20; table headings
are 12/16 semibold, headings are 24/32, and metrics are 32/40 semibold.

- Focus: every interactive element receives a 2 px `#0F766E` outline with a
  2 px offset. Never remove focus without replacing it.
- Score bands: 1–33 `Needs attention`, 34–66 `Developing`, 67–100 `High`.
  Include the score and label; colour alone cannot encode the state.
- Gender chips use a visible text label and standard capitalization.
- Sorting: sortable headers are buttons with a visible arrow and `aria-sort`.
- Selected filters appear below the toolbar as removable chips; `Clear all`
  returns to `page=1` and removes every filter parameter.

## States

| State | Required rendering |
| --- | --- |
| Loading | Preserve panel height. Four metric skeleton blocks and eight table row skeletons; no fake values. |
| Empty | `No customers match these filters.` Include `Clear all filters`; keep search/filter controls available. |
| Initial empty dataset | `No customers yet.` Include `Add customer`. This state only applies when no filters are active. |
| Error | Inline alert within the failed region with useful API detail and Retry; customer errors must not remove the metric cards. |
| Creating | Keep the form open and button disabled; handle 422 per field and attach 409 to `customer_code` as `This customer code already exists.` |
| Deleting | Confirmation dialog names `customer_code`; disable destructive button while pending; restore row and show an inline/toast error if it fails. |

## Form validation

- `customer_code`: required, 1–8 characters, treated as a string so leading
  zeroes survive.
- `gender`: exactly `Male` or `Female`.
- `age`: integer 0–130.
- `annual_income_k`: integer ≥ 0 and labelled `Annual income (k$)`.
- `spending_score`: integer 1–100.
- Translate generic 422 details into field messages, but retain server detail in
  an expandable technical section for troubleshooting.

## Accessibility and quality acceptance

- WCAG AA contrast, visible keyboard focus, and a logical heading hierarchy.
- Real `table`, `thead`, `th scope="col"`, and `tbody` semantics; caption can be
  visually hidden. Do not build the table from generic `div` elements.
- Icons used without text need accessible names; decorative icons are hidden.
- Announce result counts, create/delete completion, and errors through polite
  live regions. Move focus to the first invalid form field after submit.
- A frontend implementation is accepted when all existing API parameters and
  validation rules in the table above are represented exactly, loading/empty/
  error states can be demonstrated, query state is deep-linkable, and the page
  at 360 px is operable without clipping controls.

## Implementation order

1. Establish tokens and the responsive shell.
2. Add a typed API client for the three initial reads.
3. Implement query-string state, table, filters, sorting, and pagination.
4. Implement create validation and delete confirmation against existing routes.
5. Add loading/empty/error state stories and accessibility tests.
