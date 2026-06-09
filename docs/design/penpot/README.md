# Shopping Customers - Penpot Design Reference

Stakeholder: Mary

Developer-ready first-page UI/UX reference for the Shopping Customers API.

- Source branch: `task002/shopping-api-dataset3`
- Design branch: `kindle-aplha-prototype-penpot`
- Scope: first page only
- Public Penpot share: [Customer Directory prototype](https://design.penpot.app/#/view/8344a9c9-994c-8094-8008-267c16d0d3a6?page-id=8344a9c9-994c-8094-8008-267c16d0d3a7&index=0&share-id=8344a9c9-994c-8094-8008-267c294600df)

## Handoff Files

| Artifact | Purpose |
| --- | --- |
| [first-page.svg](./first-page.svg) | Editable vector canvas that can be imported into Penpot. |
| [first-page-spec.md](./first-page-spec.md) | Layout, responsive behavior, states, accessibility and API mapping. |
| [design-tokens.json](./design-tokens.json) | Design-token source for Penpot Tokens or frontend variables. |
| [prototype/index.html](./prototype/index.html) | Browser reference with filter and create-customer interactions. |
| [prototype/first-page.png](./prototype/first-page.png) | Reviewed desktop snapshot of the reference implementation. |

## Direction

The current repository is an API-only FastAPI service over the Mall Customer
Segmentation dataset. The first page is therefore designed as an operational
customer directory, not a marketing dashboard. It prioritizes comparison,
filtering and repeated record actions while keeping aggregate context visible.

The free [Penpot Hub Sales Dashboard example](https://penpot.app/penpothub/libraries-templates/sales-dashboard-example)
informed the basic dashboard grid.
The result is meaningfully adapted with this repository's customer fields,
actual dataset values, FastAPI query parameters, API health, create and delete
flows, spending-score visualization and implementation states.

No backend additions are required. The page maps to `GET /health`,
`GET /stats`, `GET /customers`, `POST /customers` and
`DELETE /customers/{id}`.

## Penpot Setup

1. Open the public Penpot share for visual inspection.
2. Import `first-page.svg` into a Penpot file for editable local ownership.
3. Import `design-tokens.json` with the Penpot Tokens plugin if token syncing is
   part of the frontend workflow.
4. Follow `first-page-spec.md` for behavior and API details.
5. Treat the browser prototype as the responsive rendering reference.
