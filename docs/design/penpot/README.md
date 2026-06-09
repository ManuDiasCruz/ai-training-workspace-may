# Customer Analytics Dashboard - Penpot Design Reference

Stakeholder: Mary

Developer-ready UI/UX design reference for the first page of the Shopping
Customers API.

Related application branch: `task002/shopping-api-dataset3`

Design branch: `codex-prototype-penpot`

## Artifacts

| Artifact | Link | Purpose |
| --- | --- | --- |
| Penpot-importable canvas | [first-page.svg](./first-page.svg) | Import into Penpot as the first-page visual reference. |
| Developer spec | [first-page-penpot-spec.md](./first-page-penpot-spec.md) | Layout, component mapping, states, accessibility and implementation notes. |
| Design tokens | [design-tokens.json](./design-tokens.json) | Token source for Penpot Tokens import or a frontend token pipeline. |
| Static prototype | [prototype/index.html](./prototype/index.html) | Browser-rendered first page for spacing, colors and behavior review. |

## Design Direction

The application is currently an API-only FastAPI service over the Mall Customer
Segmentation dataset. This design creates a first-page customer analytics
dashboard that lets an analyst inspect dataset health, browse customers, search,
filter, sort, create and delete customer records.

The free Penpot Hub "Sales dashboard example" was used only as a structural
starting point. The result is customized for this repository with a new
information model, customer-specific table fields, spending-score indicators,
API health state, FastAPI query parameter mapping and explicit loading, empty
and error states.

## Penpot Use

1. Open Penpot and create a file named "Shopping Customers - Dashboard".
2. Import [design-tokens.json](./design-tokens.json) in the Tokens panel.
3. Import [first-page.svg](./first-page.svg) as the first page canvas.
4. Use [first-page-penpot-spec.md](./first-page-penpot-spec.md) as the
   developer handoff source of truth.
5. Use [prototype/index.html](./prototype/index.html) for browser inspection.

No new backend endpoints are required. The page maps to `GET /health`,
`GET /stats`, `GET /customers`, `POST /customers` and
`DELETE /customers/{id}`.
