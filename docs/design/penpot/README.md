# Customer Analytics Dashboard — Penpot Design Reference

**Stakeholder: Mary**

Developer-ready UI/UX design reference for the **first page** of the
*Shopping Customers API*, delivered in **[Penpot](https://penpot.app)** (the
open-source design & prototyping platform).

| Artifact | File | Purpose |
|---|---|---|
| 📐 Spec | [`first-page-penpot-spec.md`](./first-page-penpot-spec.md) | Full developer handoff: layout, components→API map, states, a11y. |
| 🎨 Tokens | [`design-tokens.json`](./design-tokens.json) | W3C DTCG tokens — **import into Penpot** (Tokens → Import) or a CSS/Style Dictionary pipeline. |
| 🖥️ Prototype | [`prototype/index.html`](./prototype/index.html) | Runnable HTML/CSS rendering of the Penpot frame — open in a browser. |

## What this is

The app is currently API-only (FastAPI over the Mall Customer Segmentation
dataset). This reference designs a single **Customer Analytics Dashboard** page
that lets an analyst browse, filter, search, create and delete records — wired
1:1 to the endpoints that already exist (`/stats`, `/customers`, `/health`).
**No new backend endpoints are required.**

- **Related app branch:** `task002/shopping-api-dataset3`
- **This design branch:** `design/shopping-first-page-penpot`

## Starting template (Penpot Hub)

The [**Sales dashboard example**](https://penpot.app/penpothub/libraries-templates/sales-dashboard-example)
free community template was used as a structural starting point and then
**meaningfully customized** for this project (rebuilt information model, new
token system, domain-specific components, real API filters, explicit data
states). See [§9 of the spec](./first-page-penpot-spec.md#9-customization-vs-the-starting-template).
More free Penpot files: [penpot/penpot-files](https://github.com/penpot/penpot-files).

## Open the prototype

```bash
# from repo root
python -m http.server 8080
# then open http://127.0.0.1:8080/docs/design/penpot/prototype/
```

## Use the tokens in Penpot

1. Open your Penpot file → **Tokens** panel → **Import**.
2. Select [`design-tokens.json`](./design-tokens.json).
3. The color / typography / spacing / radius / shadow sets become available as
   the **"Shopping Dashboard Tokens"** collection.
