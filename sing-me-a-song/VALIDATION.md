# Validation record — updated 2026-09-02

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

## Shared-instance deployment regression checks (2026-09-02)

- Re-ran the full `npm test`: **25 backend unit, 29 real-PostgreSQL integration, and 5 frontend tests passed** (59 total). The three previously passed Cypress flows are unchanged; their latest hosted result is available in CI.
- The new migration isolation test kept a sentinel recommendation and migration history in `public`, migrated a dedicated schema, and verified both remained unchanged. It also created the same recommendation name in the isolated schema without a collision.
- The exact `start-hosted.mjs` command migrated a separate local schema, started the production server, returned healthy `/health`, and persisted a recommendation through `/api/recommendations`.
- Hosted startup rejects missing/unsafe schema names before migrations and applies the same scoped URL to migrations and runtime, preserving SSL options and limiting the pool to five connections.

## Dependency audit (unchanged)

Compatible updates were applied without `--force`. The most recent full frontend audit reported **28 findings (9 low, 7 moderate, 12 high; no critical)**. The backend audit reported **3 high findings**, all in the Prisma configuration / deepmerge-ts dependency chain (also reported by production-only audit due to the client/CLI dependency graph). The app is **not audit-clean**. Follow-up [#543](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/543) tracks the tested dependency modernization; do not interpret passing tests as security certification.

## Deployment and CI

- Live URL: [https://singasong-0827-ben.onrender.com](https://singasong-0827-ben.onrender.com).
- `render.yaml` now references the user-authorized existing Render database, with a dedicated `singasong_0827_ben` schema and database-backed health check. The shared instance lifecycle and access rules are not managed by this blueprint.
- On 2026-09-02, after sign-in and explicit approval, Render attempted the free-plan deployment of `f497e9f9ba3f28168255cde3aea25b4ef143781b`. [Blueprint sync](https://dashboard.render.com/blueprint/exs-dac6unh5efls73fb4neg/sync/exe-dac6unp5efls73fb4o6g) rejected `singasong-0827-db`: `cannot have more than one active free tier database`. Creation of `singasong-0827-ben` was canceled because database creation failed. The blueprint has no managed resources. Existing resources were untouched; no paid resources were selected. Public deployment and remote verification remain **blocked by database quota**, not authentication.
- A GitHub Actions workflow is supplied to run the checks on Node 22/Linux. Local results above are observed; consult the PR checks for the separate hosted CI result.
- The external-database blueprint created web service `srv-dac77hm10ojc73bcbasg` and built commit `56b04eb`, but startup failed with Prisma P1012 because `DATABASE_URL` was not set. No Neon database was created.
- The user subsequently requested retrying Render and authorized using an existing database if needed. `beeh-sing-me-a-song-db` is available, free, PostgreSQL 16, Oregon, with external traffic disabled and an October 2, 2026 expiration. The new blueprint uses its internal connection with a separate schema.
- Render [deployment dep-dac8ho5iedns73e1r1b0](https://dashboard.render.com/web/srv-dac77hm10ojc73bcbasg/deploys/dep-dac8ho5iedns73e1r1b0) successfully deployed `e085ee1` at 20:40 UTC on September 2. Logs confirmed schema `singasong_0827_ben`, successful migrations, and listening on Render's port 10000.
- Public HTTPS checks passed: `/health`, SPA routes, creation 201, persistence, duplicate 409, invalid input 422, upvote/read score 1, ranking/random 200, unknown API 404, and `DELETE /tests/reset` 404. The real browser displayed the API-created song, score 1 and YouTube embed.
- CI for `e085ee1` exposed an existing Supertest concurrent-request socket-close race (`ECONNRESET`); the test fixture now explicitly owns its listener for the full suite. All 29 integration tests passed locally after this repair.
- Final application commit `cbae2a18469fca1a11e51de91967822526a51b94` passed [GitHub Actions on Node 22/Linux](https://github.com/ManuDiasCruz/ai-training-workspace-may/actions/runs/33681003290), including production builds and **62 tests: 25 unit, 29 integration, 5 frontend, 3 Cypress**.
- Render [redeployment dep-dac8kulckfvc738rkmog](https://dashboard.render.com/web/srv-dac77hm10ojc73bcbasg/deploys/dep-dac8kulckfvc738rkmog) made `cbae2a1` live at 20:45 UTC. It reported no pending migrations. The verification song survived this redeploy with score 1; seven normal downvotes removed only that disposable record, and subsequent reads/votes returned 404. The browser then displayed the empty random state instead of a loading loop.
- Final documentation-only changes use Render's `[skip render]` commit marker; the verified deployed application remains `cbae2a1`.

## Follow-up issues

Each issue includes Related Branch and Next Steps sections:

- [#543 — dependency advisories](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/543)
- [#544 — anonymous API abuse prevention](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/544)
- [#545 — bounded-memory random sampling](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/545)
- [#546 — unavailable YouTube videos](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/546)
- [#547 — durable backups and monitoring](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/547)
