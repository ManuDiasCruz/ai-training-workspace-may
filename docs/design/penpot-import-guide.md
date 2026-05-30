# Penpot Import Guide

Stakeholder: Mary

Source branch: `task002/shopping-api-dataset3`
Design branch: `prototype-penpot-codex`

## Prototype Package

- First-page artifact: [shopping-customers-first-page.svg](shopping-customers-first-page.svg)
- Handoff notes: [shopping-customers-first-page-handoff.md](shopping-customers-first-page-handoff.md)
- Canvas size: `1440 x 1050`
- Scope: first page only

This design was created as a Penpot-ready reference for the Shopping Customers
API. The application repository currently exposes a FastAPI backend without a
frontend, so the first page is a developer handoff for a customer analytics
dashboard that maps directly to the existing API contract.

## Penpot Import Steps

1. Create or open the Penpot file for the Shopping Customers frontend.
2. Import `shopping-customers-first-page.svg` into the file.
3. Keep the imported canvas at `1440 x 1050` and name the board
   `Shopping Customers - First Page`.
4. Add a text note near the canvas with:
   `Stakeholder: Mary`
5. Link the Penpot share URL back into the README Design section and issue
   #95 after import.

## Developer Mapping

| UI area | API endpoint or behavior |
| --- | --- |
| KPI row | `GET /stats` |
| Customer table | `GET /customers?page=1&page_size=20` |
| Search | `GET /customers?search={query}` |
| Filters | `gender`, `min_age`, `max_age`, `min_income`, `max_income`, `min_score`, `max_score` |
| Sort controls | `sort_by` and `order` |
| New customer | `POST /customers` |
| Delete row | `DELETE /customers/{id}` |

## Implementation Notes

- Preserve API query parameter names in the UI URL state.
- Show table skeleton rows during loading.
- Use an inline empty state when filters return no records.
- Render `400`, `409`, `422` and `404` errors near the control that caused them.
- Confirm before delete actions because the backend has no restore endpoint.
- Keep the visual system restrained: white surfaces, teal primary actions,
  amber score warnings, green high-value states and red destructive actions.

No public template was used; the reference is customized around the dataset,
FastAPI endpoints and README API contract in this repository.
