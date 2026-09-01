# Validation record — 2026-09-01

## Observed local results

Environment: Windows, Node 24.19.0, npm 10.9.9 and an isolated PostgreSQL 16.14 instance. Recommended deployment/CI runtime: Node 22 LTS. No existing application database was used for tests.

| Check | Result |
| --- | --- |
| Backend `npm run build` | Passed; Prisma 6.19.3 generated and TypeScript compiled |
| Backend unit tests | 16 passed |
| PostgreSQL integration tests | 28 passed |
| Frontend component regressions | 5 passed |
| Frontend production build (`CI=true`) | Passed |
| Cypress 15.21.1 / headless Electron | 3 passed against the real API and disposable PostgreSQL database |
| Browser production-build smoke | Created and persisted a song; voted and observed score 1; directly loaded `/top`; YouTube iframe loaded |
| API readiness | `/health` returned 200 with `status: ok` |
| Test safety | Non-test database guard rejected access; disabled reset endpoint returned 404 |

**52 automated tests passed.** Cypress includes creation, voting, ranking, random selection, threshold deletion, duplicate/invalid submissions and retry after a simulated API outage. Unit/integration tests additionally cover malformed JSON, numeric bounds, concurrent creation/voting, random access beyond the latest ten, and health failure responses.

The original start command reproduced `MODULE_NOT_FOUND` for `dist/index.js`. The original tests also depended on an undeclared random-video package and used incorrect ordering/response assumptions. The repaired build/start, fixtures, contracts and test runners are committed.

## Dependency audit

Compatible updates were applied without `--force`. The most recent full frontend audit reported **28 findings (9 low, 7 moderate, 12 high; no critical)**. The backend audit reported **3 high findings**, all in the Prisma configuration / deepmerge-ts dependency chain (also reported by production-only audit due to the client/CLI dependency graph). The app is **not audit-clean**. Follow-up [#543](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/543) tracks the tested dependency modernization; do not interpret passing tests as security certification.

## Deployment and CI

- The production build was run and exercised locally, not on a public hosting service.
- `render.yaml` defines the intended Node/PostgreSQL deployment, migrations, runtime configuration and `/health` check.
- Public deployment and remote frontend/backend integration verification are **blocked by missing hosting authentication**. The available Render browser session was at the sign-in page; no hosting credentials were configured. No deployed URL exists for this work and no paid resources were created.
- A GitHub Actions workflow is supplied to run the checks on Node 22/Linux. Local results above are observed; consult the PR checks for the separate hosted CI result.

## Follow-up issues

Each issue includes Related Branch and Next Steps sections:

- [#543 — dependency advisories](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/543)
- [#544 — anonymous API abuse prevention](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/544)
- [#545 — bounded-memory random sampling](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/545)
- [#546 — unavailable YouTube videos](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/546)
- [#547 — durable backups and monitoring](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/547)
