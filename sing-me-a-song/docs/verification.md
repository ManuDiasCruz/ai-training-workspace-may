# Verification record

Local verification: 2026-09-01. Hosted verification: 2026-09-02. Branch: `0827-beeh-singasong`.

## Environment and scope

- Windows, Node 22.23.2, npm 10.9.8, isolated PostgreSQL 16.14.
- Separate development and `_test` databases created for this task; no existing user database was reset.
- Only the supplied source project was investigated. The destination repository's unrelated files were preserved, not used as reference implementations.

## Observed results

| Check | Result |
| --- | --- |
| Original backend startup | Reproduced missing `dist/index.js` failure |
| Original backend tests | Reproduced module/test setup failure; factory also required an undeclared package |
| Backend unit suite | 14 passed |
| Backend integration suite | 33 passed against real PostgreSQL |
| Frontend hook/page regressions | 9 passed |
| Backend production build | Passed with Prisma 6.19.0 and TypeScript 5.9.3 |
| Frontend production build | Passed with `CI=true` (warnings treated as errors) |
| Production API smoke | Passed: health, SPA routes, creation, list, votes, top, random, removal, and disabled reset route |
| Production browser | Creation, score changes, Top/Random navigation, direct `/random` reload, and YouTube embed rendering verified |
| Database test guard | Refused a non-`_test` database URL before migrations or data changes |
| Environment-file exclusion | Real `.env` and `.env.test` ignored; only placeholder examples tracked |
| Local Cypress | 4 passed against the real development frontend, test API, and PostgreSQL using headless Electron |
| Hosted deployment | **Passed on Render, 2026-09-02:** build, migrations, startup, database health, live API smoke, and browser data/navigation checks |

The YouTube iframe and controls loaded. This is not a guarantee of playback for every video, region, or embedding permission. The test suites deliberately use a fixed syntactically valid URL instead of fetching random external music links.

The production smoke script creates and cleans up its own uniquely named record. The synthetic manual-browser record was also removed. Cypress initially exceeded its 30-second first-start verification timeout; retrying with `CYPRESS_VERIFY_TIMEOUT=120000` verified the browser and all four specs passed. Verification was not skipped. Total passing tests: **60**. [Linux CI also passed](https://github.com/ManuDiasCruz/ai-training-workspace-may/actions/runs/33517747201) on `019beb9`, including clean setup, all 60 tests, both builds, Cypress, and the production smoke check.

The first clean Linux CI run exposed missing generated Prisma model types: the dependency postinstall hook did not find the nested schema when installation used `npm --prefix`. Setup now explicitly runs the backend's `db:generate` script before tests or development startup. This fixes the actual clean-install path, not just the order of CI checks.

## Dependency audits

The final frontend production-only audit (`npm audit --omit=dev`) reports **zero findings**. The full frontend tree still reports **35 findings: 10 low, 7 moderate, 16 high, 2 critical**, in retained build/test tooling. Do not confuse a production-only audit with an audit of the whole repository.

The backend production-only audit reports **5 high findings** in Prisma's CLI dependency tree (`deepmerge-ts` and `effect`, including parent packages). These are present because deployment runs migrations with the CLI. No untrusted Prisma configuration or Effect RPC is used by the app, but that scope observation does not dismiss the advisories. Non-breaking audit fixes were applied; forced major upgrades/downgrades were not.

Follow-ups: [frontend tooling](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/538) and [Prisma CLI advisories](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/539). Audit counts are point-in-time results and can change as new advisories are published.

## Hosted deployment — 2026-09-02

- Application: **https://beeh-sing-me-a-song.onrender.com**.
- [Render Blueprint](https://dashboard.render.com/blueprint/exs-dac6u4rm8hqs73a3v0dg): `0827-beeh-singasong`, using `sing-me-a-song/render.yaml` from the assigned branch.
- [Initial successful deployment](https://dashboard.render.com/web/srv-dac6v461a4lc739f3scg/deploys/dep-dac6v4e1a4lc739f3sp0): commit `019beb9db29f89bff474ecaebb4a0a89bff29d23`; Render reported **Deploy succeeded / Live**, with a duration of 1m49s. The first hosted build succeeded without additional application-code fixes.
- New resources only: free Node service `beeh-sing-me-a-song` and free PostgreSQL 16 database `beeh-sing-me-a-song-db`, both in Oregon. Existing services were not modified. No paid plan was enabled.
- Render applied migration `20220503164046_create_recommendations`, then started `dist/server.js` on its supplied port 10000. `/health` returned HTTP 200 with `{"status":"ok"}`.
- `DATABASE_URL` remains a managed secret binding. PostgreSQL's resource-specific inbound rules block external internet connections; the web service uses the private database connection. Credentials were not copied into Git or documentation.

### Remote checks observed

| Check | Result |
| --- | --- |
| Production smoke against the actual HTTPS origin | Passed health, `/`, `/top`, `/random`, create, list, upvote, ranking, random retrieval, downvote deletion, and disabled reset route |
| Browser Home | Loaded the live database fixture, its score, controls, and YouTube embed |
| Browser Top and Random | Rendered the fixture and persisted score 1 after an API upvote; direct `/top` loading and `/random` reload passed |
| Browser empty state | After fixture cleanup, Another song displayed the expected no-recommendations message |
| Invalid requests | Malformed JSON returned 400; invalid ID and top amount returned 422 |
| Sensitive/test paths | `/.env`, `/back-end/.env`, and `/tests/reset` returned 404 |
| Test data cleanup | Both uniquely named hosted test records were removed through normal downvotes; no database reset or unrelated-record deletion was used |

The hosted smoke script exercised mutations through HTTP. Browser checks verified the deployed UI's reads, navigation, score display, embed rendering, and empty state; browser form submission and vote clicks were covered by the already-passing local/Linux Cypress runs. An initial in-app-browser `/top` reload encountered `ERR_CONNECTION_CLOSED`; direct loading in a fresh tab succeeded, and the subsequent `/random` reload and HTTP checks passed. No persistent application failure was established. YouTube playback availability remains outside the application's control.

### Operational limits

Render reports that this free database **expires on October 2, 2026**, and will be deleted unless upgraded. Free web instances sleep during inactivity and can delay initial requests by 50 seconds or more. Warm the health endpoint with `node scripts/wait-for.mjs https://beeh-sing-me-a-song.onrender.com/health` before running the smoke script, whose individual requests time out after 30 seconds.

[Issue #575](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/575) tracks durable hosting, budget approval, backups, and a tested restore before expiry. Abuse controls and the dependency advisories above remain follow-up work; this is an evaluation deployment, not a claim of production-grade operational readiness.
