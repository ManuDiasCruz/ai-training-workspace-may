# Customer Overview — Penpot Design Reference

**Stakeholder: Cora**

Developer-ready design reference for the **first page** of a UI on top of the
**Shopping Customers API** (Mall Customer Segmentation dataset). This is the
deliverable for Sprint task **#4**.

- **Reference app branch:** [`task002/shopping-api-dataset3`](../../../) — the FastAPI
  service this design is built against.
- **Design branch:** `O48-H-prototype-penpot`
- **Penpot prototype (public view link):** <https://design.penpot.app/#/view?file-id=cf421b06-918b-81ac-8008-4bf96da5d669&page-id=cf421b06-918b-81ac-8008-4bf96da5d66a&section=interactions&index=0&share-id=279d72fe-2334-8043-8008-4bfe6fa40647>

## The page

A **Customer Overview** analytics dashboard — the natural first screen for this
dataset. It contains, top to bottom:

1. **Top bar** — page title, live `GET /health` status pill, search, *New customer*.
2. **KPI row** — the four headline figures from `GET /stats`
   (total customers, avg age, avg annual income, avg spending score).
3. **Insight row** — gender-split donut (`by_gender`) and a five-segment
   *spending-score vs annual-income* scatter (the classic Mall segmentation).
4. **Customers table** — filter bar wired to the exact `GET /customers` query
   params, a sortable/paginated table, and a per-row spending-score band.

## Files

| File | Purpose |
|------|---------|
| [`customer-segmentation-dashboard.svg`](customer-segmentation-dashboard.svg) | The Penpot-importable canvas (source of the prototype). |
| [`prototype/index.html`](prototype/index.html) | Runnable, inspectable HTML/CSS reference of the same page. |
| [`implementation-spec.md`](implementation-spec.md) | Region-by-region mapping to FastAPI endpoints + build states. |
| [`design-tokens.json`](design-tokens.json) | Colours, type, spacing and radius tokens (Penpot tokens format). |

## Working with the Penpot file

The file was created in Penpot from the `customer-segmentation-dashboard.svg`
canvas. A public/community Penpot template (the *Wireframe / Prototype* starter)
informed the base grid, but the page has been fully customised for this project:
the **ShopSense / Customer Intelligence** brand, an indigo + amber analyst palette,
the dataset's real fields and sample rows, live API-health feedback, the service's
exact filters and sort options, spending-score bands, and the segmentation scatter.

To iterate:
1. Open the Penpot view link above (read-only) or duplicate it into your team.
2. Re-import `customer-segmentation-dashboard.svg` if you want the raw layers.
3. Keep tokens in sync with `design-tokens.json`.

## Scope

Per the sprint task, **only the first page** is delivered, and it maps solely to
endpoints that exist today. See `implementation-spec.md` for the full handoff.
