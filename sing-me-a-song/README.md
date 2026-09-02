# Sing Me a Song

Share YouTube song recommendations, vote them up/down, browse the latest ten or top-ranked songs, and discover a random song. Recommendations scoring below -5 are deleted.

Imported from [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song), source commit `46e4e117be89041aa1cc492558357d89ddb0306a`, into `sing-me-a-song/` on branch `0827-ben-singasong`. No unrelated repository code was used. The destination's existing files and the original [frontend documentation](front-end/README.md) are preserved.

## Structure and flow

- `front-end/`: React 18, React Router, styled-components, Axios, ReactPlayer; home, top and random views.
- `back-end/`: Express/TypeScript routes → validation/controllers → recommendation service → Prisma → PostgreSQL.
- `back-end/prisma/`: original schema and versioned SQL migration.
- `back-end/tests/`: unit tests and real PostgreSQL integration tests.
- `front-end/src/App.test.js`: frontend regression coverage; `front-end/cypress/e2e/spec.recommendation.cy.js`: active browser tests.
- `../render.yaml`: a Node web service and PostgreSQL deployment blueprint.
- `../.github/workflows/sing-me-a-song.yml`: build, database, component and browser checks.

Production Express serves the React build and `/api/recommendations` from one origin. Original `/recommendations` API URLs remain supported. Development uses React's `/api` proxy to port 5000.

## Requirements

Use Node.js **22.12+ (22 LTS recommended)** and npm 10+, plus PostgreSQL 16. `.nvmrc` selects Node 22; the supported range also includes Node 24. The checked-in lockfiles are required. No YouTube API key is needed.

Commands below start in this `sing-me-a-song` directory, not the repository root. Do not run these commands against an unrelated project or production database.

## Local setup

1. Create two PostgreSQL databases using your local PostgreSQL account:

   ```sh
   createdb -U postgres sing_me_a_song
   createdb -U postgres sing_me_a_song_test
   ```

2. Copy `back-end/.env.example` to `back-end/.env`, and `back-end/.env.test.example` to `back-end/.env.test`. Replace `CHANGE_ME` and adjust host, port and user locally. The second URL **must** reference the disposable `_test` database, never your normal database.
3. Install, migrate and build:

   ```sh
   npm run setup
   npm run db:migrate
   npm run build
   npm start
   ```

4. Open [localhost:5000](http://localhost:5000). `/health` should return `{"status":"ok"}`. Existing data is preserved by `prisma migrate deploy`; there is no automatic seed or reset.

For development, run `npm run dev --prefix back-end` and, in a second terminal, `npm start --prefix front-end`. React runs on port 3000 and proxies to backend port 5000. If changing the backend development port, change the frontend `proxy` value accordingly. Environment values already set by the shell or host override dotenv files.

## Environment variables

| Variable | Location | Purpose / default |
| --- | --- | --- |
| `DATABASE_URL` | Backend only, required | Private PostgreSQL URL. Use the provider's SSL options if required. Never expose it through React variables. |
| `PORT` | Backend | HTTP port, default `5000`; hosts may inject it. |
| `NODE_ENV` | Backend/build | `development`, `test`, or `production`. |
| `CORS_ORIGINS` | Backend | Optional comma-separated frontend origins for split hosting. Default permits `http://localhost:3000`; production same-origin requests need no CORS configuration. |
| `ENABLE_TEST_ROUTES` | Backend | Default off. Only exact `true` enables `/tests/reset`, and startup then requires `NODE_ENV=test` and a URL whose database name ends in `_test`. Never enable in production. |
| `REACT_APP_API_BASE_URL` | Frontend build-time | Empty/unset uses `/api`. For split hosting use `https://your-api-host/api`, allow the frontend origin in CORS, and rebuild. This value is public, not a secret. |
| `CYPRESS_BASE_URL` | Test process | Full local test-server origin, default `http://localhost:5000`. |
| `CYPRESS_INSTALL_BINARY` | Hosting build | Set to `0` to skip downloading the test browser on the deployment host. Do not set this when installing for browser tests. |

`.env`, `.env.test`, logs, dependencies and build outputs are ignored; only redacted example files are tracked. Store hosting credentials in the provider's secret settings. Do not paste connection URLs into issues, PRs, logs or screenshots.

## Tests

```sh
npm run db:migrate:test --prefix back-end
npm test
```

`npm test` runs backend unit/integration tests and frontend component tests. Integration tests **truncate the disposable test database before each test**. Both test migration and test reset utilities fail closed without `NODE_ENV=test` and a database name ending in `_test`. Unit tests need no running database. Test commands work on Windows and Unix; the original shell-only assignment and missing seed command were removed.

For Cypress, build the app first, stop any normal API using port 5000, and set `ENABLE_TEST_ROUTES=true` **only in `back-end/.env.test`**. Start `npm run dev:test --prefix back-end`, then run `npm run test:e2e --prefix front-end`. Reset that flag to `false` afterward. Cypress resets all data in that test database. The active spec covers real creation/voting/ranking/random/deletion, duplicate/invalid submissions and recovery from a simulated failed read. Historical tutorial/spec files are retained from upstream but intentionally excluded from the active `specPattern`.

## Deployment (Render)

**Status (2026-09-02):** Render sign-in and the free-plan deployment were approved. Render rejected PostgreSQL creation because this workspace already has one active free-tier database; web-service creation was canceled. No existing resources were changed and no paid plan was selected. Public deployment and remote verification remain pending an available PostgreSQL database. A locally running production build is not a public deployment.

1. Sign in to Render and connect this GitHub repository.
2. Create a Blueprint from branch `0827-ben-singasong`, using root `render.yaml`. Review the resources and current pricing before confirming.
3. The blueprint provisions PostgreSQL, injects its private connection URL as `DATABASE_URL`, installs both projects, builds them, runs `prisma migrate deploy`, and starts Express. The service root is `sing-me-a-song`.
4. Keep `ENABLE_TEST_ROUTES=false`; do not configure a frontend database variable or commit provider credentials. Same-origin `/api` avoids hardcoded deployment hostnames.
5. Wait for `/health` to pass. Open the assigned HTTPS URL and repeat the checklist below. If health is 503, check database provisioning and migrations; if startup exits, check the private connection settings in the provider dashboard.

The blueprint selects free resources as a demo starting point. Render's free database is time-limited and free web services can sleep; choose durable paid database storage/backups before relying on it. No paid resources were purchased. See [Render's Express deployment guide](https://render.com/docs/deploy-node-express-app), [Blueprint reference](https://render.com/docs/blueprint-spec), and [free-tier limitations](https://render.com/docs/free).

### Post-deployment verification checklist

- `/health` returns 200 and `{"status":"ok"}`; unknown `/api` paths return 404, not HTML.
- `/`, `/top` and `/random` work on direct navigation and refresh.
- Submit a uniquely named YouTube video; reload and verify persistence.
- Duplicate names show a conflict; invalid video links are rejected without clearing input.
- Upvote/downvote and confirm score changes. Using only the disposable verification song, six downvotes from score 0 remove it.
- Empty random results show an empty state; failed requests show retry controls.
- Confirm `DELETE /tests/reset` is 404 in production, and inspect browser console/network for application errors.
- Check data persists across a service restart. Do not reset or truncate a deployed database to test it.

## Repairs made

- Corrected the production entrypoint, added a real TypeScript build, repaired ESM imports, loaded dotenv safely, and added graceful shutdown and startup diagnostics.
- Updated Prisma/client together, aligned Jest/ts-jest/TypeScript, replaced the broken development runner, removed undeclared fixture dependencies and repaired asynchronous tests.
- Preserved the original database schema/migration and API paths; added same-origin `/api`, SPA routes, bounded requests, CORS configuration and database-backed health.
- Validated numeric IDs/ranking limits, trimmed names and checked actual YouTube video URL forms. Malformed JSON is 400; duplicate database races are 409; deleted targets are 404.
- Kept atomic vote increments and prevented threshold deletion from deleting a concurrently recovered score. Random sampling now includes songs beyond the latest ten; ranking ties are deterministic.
- Added UI errors/retries, preserved failed form input, prevented failed-vote success callbacks, fixed empty/deleted random results, labelled form/vote buttons and restored visible player controls.
- Applied compatible dependency security updates and replaced obsolete Cypress. No force-upgrade or framework rewrite was applied.

## Verification and known limitations

See [VALIDATION.md](VALIDATION.md) for the final observed test results and deployment status.

- Remaining dependency advisories affect the legacy CRA/React Router toolchain and Prisma configuration dependency graph. The project is **not audit-clean**; plan tested upgrades instead of `npm audit fix --force`.
- Anonymous recommendation/voting APIs have no per-user voting limits, authentication or abuse throttling. CORS is not authorization.
- Random sampling currently loads the selected score bucket into memory; replace with database-side count/offset sampling when scaling.
- Syntactically valid YouTube links can still be unavailable, private, region-restricted or disallow embedding. Video availability is controlled by YouTube and is not guaranteed by these tests.
- Configure durable backups, restore drills and uptime alerts before a production rollout. Hosting completion remains a required follow-up, not a verified result.
