# Shopping Customers First Page Design Handoff

Stakeholder: Mary

Source branch: `task002/shopping-api-dataset3`
Design branch: `prototype-penpot-codex`

## Prototype Reference

- Prototype artifact: [shopping-customers-first-page.svg](shopping-customers-first-page.svg)
- Penpot import guide: [penpot-import-guide.md](penpot-import-guide.md)
- Intended Penpot use: import the SVG into Penpot as the first-page prototype canvas.
- Canvas: desktop dashboard, `1440 x 1050`.
- Scope: first page only.

The Penpot MCP execution endpoint is available, but the live plugin instance was
not connected for this user token during the handoff pass. This branch therefore
includes an import-ready Penpot reference package: the first-page SVG, import
steps, visual tokens, API mapping and implementation notes. After importing the
SVG into Penpot, replace this note with the live Penpot share URL in the README
and related GitHub issue.

## Product Direction

The API exposes the Mall Customer Segmentation dataset. The first page should make
that dataset useful to an analyst or operator before any deep reporting is built.
The proposed UI is a quiet customer analytics dashboard with three main jobs:

- Show aggregate health from `GET /stats`.
- Let users search, filter, sort and page through `GET /customers`.
- Provide obvious entry points for `POST /customers` and `DELETE /customers/{id}`.

## Layout

- Left navigation: product identity, active Customers item, secondary navigation.
- Header: page title, dataset context, global search, export button, New customer action.
- KPI row: total customers, average age, average income, average spending score.
- Filter rail: gender, age range, income range, score range, sort control.
- Customer table: customer code, gender, age, income, score, segment and row actions.
- Side panel: selected customer summary, API callout and implementation notes.

## Visual Tokens

Use these values as the first implementation pass:

| Token | Value |
| --- | --- |
| Page background | `#F6F7FB` |
| Surface | `#FFFFFF` |
| Primary | `#0F766E` |
| Primary dark | `#0B5E58` |
| Accent | `#D97706` |
| Text strong | `#111827` |
| Text muted | `#667085` |
| Border | `#DDE3EA` |
| Success | `#15803D` |
| Warning | `#B45309` |
| Danger | `#B42318` |
| Radius | `8px` |
| Card shadow | `0 12px 30px rgba(15, 23, 42, 0.08)` |

## API Mapping

| UI element | API behavior |
| --- | --- |
| KPI cards | `GET /stats` |
| Table data | `GET /customers?page=1&page_size=20` |
| Search input | `GET /customers?search={query}` |
| Gender filter | `gender=Male` or `gender=Female` |
| Age range | `min_age` and `max_age` |
| Income range | `min_income` and `max_income` |
| Score range | `min_score` and `max_score` |
| Sort menu | `sort_by=id|age|annual_income_k|spending_score|customer_code` and `order=asc|desc` |
| New customer | `POST /customers` with inline validation |
| Delete row action | `DELETE /customers/{id}` with confirmation |

## Frontend Notes

- Keep filters, search, sorting and pagination in the URL query string.
- Preserve the API parameter names exactly to simplify endpoint integration.
- Show loading skeletons inside the table body, not as a full page blocker.
- Use a compact empty state when filters return zero rows.
- Display `400`, `409`, `422` and `404` API errors inline near the action that caused them.
- Do not use browser alerts for create or delete flows.
- Default table density should fit at least 10 rows at common laptop heights.
- Treat the side panel as a selected-row summary in the first implementation; a full detail drawer can come later.
