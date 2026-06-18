# Customer Intelligence — Penpot design reference

Stakeholder: Mary

This directory is the developer handoff for the first page of the Shopping
Customers API on application branch `task002/shopping-api-dataset3`. The design
assets live on `claude-prototype-penpot`.

## Design references

| Artifact | Purpose |
| --- | --- |
| [Public Penpot view](https://design.penpot.app/#/view/8344a9c9-994c-8094-8008-267c16d0d3a6?page-id=8344a9c9-994c-8094-8008-267c16d0d3a7&index=0&share-id=8344a9c9-994c-8094-8008-267c294600df) | Shareable baseline for structure, inspectable in Penpot. |
| [customer-intelligence.svg](./customer-intelligence.svg) | Final 1440 px canvas. Import this into Penpot to use the customized visual reference. |
| [prototype/index.html](./prototype/index.html) | Runnable, responsive browser reference for developer inspection. |
| [implementation-spec.md](./implementation-spec.md) | Component dimensions, API mappings, behavior, states, and acceptance criteria. |
| [design-tokens.json](./design-tokens.json) | Canonical token names and values. |

## Direction

The page serves an internal retail analyst who needs the dataset's condition and
customer segments at a glance, then needs to narrow and act on records without
switching contexts.

The linked public Penpot file is a useful first-page dashboard starting frame.
The version in this branch is meaningfully adapted to the actual API:

- real statistics from `GET /stats`, including the gender split;
- the exact query contract supported by `GET /customers`;
- real `CustomerOut` fields and sample values from `Shopping_data.csv`;
- visible spending-score bands with text labels rather than colour alone;
- API health, add-customer, and delete-record entry points;
- a new navy/teal/slate design system, denser analyst-focused hierarchy, and a
  filter summary row that does not appear in the starting frame;
- explicit loading, empty, error, destructive confirmation, focus, and narrow
  viewport behavior in the handoff spec.

## Open in Penpot

1. Open the [public Penpot view](https://design.penpot.app/#/view/8344a9c9-994c-8094-8008-267c16d0d3a6?page-id=8344a9c9-994c-8094-8008-267c16d0d3a7&index=0&share-id=8344a9c9-994c-8094-8008-267c294600df).
2. For the final visual direction, create or duplicate a Penpot file, choose
   **File → Import**, and import `customer-intelligence.svg` as the first page.
3. Name the board `01 · Customer Intelligence — Desktop` and preserve the layer
   names from the SVG. Apply the values in `design-tokens.json` as shared tokens.
4. Use the states and breakpoint rules in `implementation-spec.md` during
   implementation; the static SVG intentionally depicts only the loaded
   first-page state requested in scope.

The repository artifacts are the handoff source of truth when the public share
and this branch differ.
