# Verification record

Date: 2026-09-01. Branch: `0827-beeh-singasong`.

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
| Hosted deployment | **Not performed: Render is signed out and no hosting credential is configured** |

The YouTube iframe and controls loaded. This is not a guarantee of playback for every video, region, or embedding permission. The test suites deliberately use a fixed syntactically valid URL instead of fetching random external music links.

The production smoke script creates and cleans up its own uniquely named record. The synthetic manual-browser record was also removed. Cypress initially exceeded its 30-second first-start verification timeout; retrying with `CYPRESS_VERIFY_TIMEOUT=120000` verified the browser and all four specs passed. Verification was not skipped. Total passing tests: **60**. The Linux CI workflow is additional verification and its remote status should be checked separately.

The first clean Linux CI run exposed missing generated Prisma model types: the dependency postinstall hook did not find the nested schema when installation used `npm --prefix`. Setup now explicitly runs the backend's `db:generate` script before tests or development startup. This fixes the actual clean-install path, not just the order of CI checks.

## Dependency audits

The final frontend production-only audit (`npm audit --omit=dev`) reports **zero findings**. The full frontend tree still reports **35 findings: 10 low, 7 moderate, 16 high, 2 critical**, in retained build/test tooling. Do not confuse a production-only audit with an audit of the whole repository.

The backend production-only audit reports **5 high findings** in Prisma's CLI dependency tree (`deepmerge-ts` and `effect`, including parent packages). These are present because deployment runs migrations with the CLI. No untrusted Prisma configuration or Effect RPC is used by the app, but that scope observation does not dismiss the advisories. Non-breaking audit fixes were applied; forced major upgrades/downgrades were not.

Follow-ups: [frontend tooling](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/538) and [Prisma CLI advisories](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/539). Audit counts are point-in-time results and can change as new advisories are published.

## Deployment handoff

`render.yaml` defines a same-origin Node web service, managed PostgreSQL, secret database binding, migration-before-start, and `/health`. No real hosted URL has been returned and no remote success is claimed.

To finish: authenticate Render (or supply access to another suitable Node/PostgreSQL host), deploy the requested branch using the documented Blueprint path, then repeat the browser and smoke checks against the actual hosted origin. Record that URL, deployment result, and remote checks here and in the PR before marking deployment complete. Free-tier database expiry, backups, and public abuse controls need explicit consideration before ongoing use.
