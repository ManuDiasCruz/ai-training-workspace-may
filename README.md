# Sing Me a Song

Sing Me a Song is a full-stack music recommendation application. Users submit a name and YouTube URL, browse the ten most recent recommendations, vote them up or down, see the highest-scoring entries, and request a weighted random recommendation. A recommendation is removed after its score drops below `-5`.

This branch imports the original [sing-me-a-song source](https://github.com/ManuDiasCruz/sing-me-a-song). The original Create React App documentation remains in [`front-end/README.md`](front-end/README.md).

## Project layout and flow

- `front-end/`: React 18, React Router, Axios, styled-components, React Player, and Cypress.
- `back-end/`: Express 4 and TypeScript API, Joi request validation, Prisma Client, and PostgreSQL migrations.
- `render.yaml`: a single same-origin Render web service plus a managed PostgreSQL database.
- `.github/workflows/ci.yml`: build, unit/API contract, PostgreSQL integration, and Cypress flow checks.

The browser calls `/recommendations`. The router delegates to the controller, service, repository, and Prisma. `GET /recommendations` returns the ten newest entries; `GET /recommendations/top/:amount` returns a bounded score-ordered list; `GET /recommendations/random` uses the original 70/30 score-bucket selection and falls back to available entries. `POST /recommendations` returns the created record. Votes use `POST /recommendations/:id/upvote` and `/downvote`.

## Local setup

Prerequisites: Node.js 22 (the pinned version is in `.node-version`), npm, and a PostgreSQL server. Create **two separate databases**: one for development and a disposable one for tests. Do not point the test configuration at production or development data; the integration and Cypress reset flows truncate the recommendations table.

1. Copy `back-end/.env.example` to `back-end/.env` and replace `USER`, `PASSWORD`, host, and database with credentials you control. Copy `back-end/.env.test.example` to `back-end/.env.test` and use the separate test database. These real files are ignored by Git.
2. Copy `front-end/.env.example` to `front-end/.env`. Its local API base URL is `http://localhost:5000`.
3. Install and migrate the API:

   ```bash
   cd back-end
   npm ci
   npm run db:migrate:deploy
   npm run dev
   ```

4. In another terminal, start the frontend:

   ```bash
   cd front-end
   npm ci
   npm start
   ```

Open `http://localhost:3000`. The API listens on `http://localhost:5000`. `GET /health` checks the HTTP process; `GET /ready` also checks database connectivity.

### Environment variables

| Location | Variable | Purpose |
| --- | --- | --- |
| API | `DATABASE_URL` | Required PostgreSQL connection URL. Keep the real value in an ignored environment file or hosting secret store. |
| API | `PORT` | HTTP port; defaults to `5000`. A host can inject its own port. |
| API | `CORS_ORIGIN` | Comma-separated allowed browser origins; defaults to `http://localhost:3000`. CORS is not authentication. |
| API | `MODE` | Set to `TEST` only for an isolated test server. The destructive `/tests/reset` route is never mounted when `NODE_ENV=production`. |
| API | `SERVE_FRONTEND` | Set to `true` to serve `front-end/build` and React Router fallback from the API. |
| frontend | `REACT_APP_API_BASE_URL` | Local or separately hosted API origin. Omit it for the same-origin Render build. It is embedded in the public browser bundle and must never contain a secret. |

## Validation

From `back-end`:

```bash
npm run build
npm run test:unit
npm run db:migrate:test
npm run test:integration
```

`test:unit` uses a credential-free placeholder URL because Prisma 3 initializes its engine, but repository calls are mocked. Integration tests require the disposable `.env.test` database. For browser tests, run `npm run dev:test` in `back-end`, run the frontend with its local API URL, and then run `npm run test:e2e` in `front-end`. The test server's reset endpoint is `DELETE /tests/reset`.

To smoke-test the same-origin production layout locally, build both applications, set `SERVE_FRONTEND=true` and a valid `DATABASE_URL`, then run `npm start` from `back-end`. `/`, `/top`, and `/random` should return the React application, while API paths remain under `/recommendations`.

## Deployment

The included Render Blueprint is a simple preview deployment for this stack. In the Render Dashboard, create a Blueprint from `ManuDiasCruz/ai-training-workspace-may`, select branch `731-deh-singmeasong`, and review `render.yaml`. It creates a PostgreSQL database, injects its internal connection string as `DATABASE_URL`, builds both applications, applies committed Prisma migrations at web-service startup, and serves the React build from the Express origin. No database credential is stored in this repository. After deployment, verify `/health`, `/ready`, the home page, create, vote, top, random, and direct navigation to `/random`.

The Blueprint deliberately selects free preview instances. A free Render web service spins down when idle, and a free Render Postgres database expires after 30 days and has no backups. Upgrade to an appropriate paid plan before relying on retained data. Paid web services can move `prisma migrate deploy` to a `preDeployCommand`; the free plan does not support that command. Review current Render pricing and limitations before creating resources.

## Repairs in this branch

- Added a real backend compile command and corrected the production entry point from nonexistent `dist/index.js` to `dist/server.js`.
- Loaded local environment configuration, corrected extensionless ESM imports, added graceful shutdown, health/readiness routes, and a guarded same-origin frontend deployment path.
- Validated positive integer route parameters and bounded top-list requests; tightened YouTube host validation; mapped unique-write races and missing records to appropriate API statuses.
- Returned the created recommendation from `POST /recommendations` and made top-list ties deterministic.
- Repaired the ESM test factory, awaited rejection assertions, restored mocks, fixed integration ordering assumptions, and added API contract regression tests.
- Replaced broken Cypress example/obsolete suites with focused create, vote, timeline, validation, and empty-state flows, and corrected the reset URL.
- Added request timeouts, retry/error/empty states, success-aware refreshes, retained failed form input, accessible submit/vote controls, and duplicate-vote protection.
- Added safe environment examples, locked runtime/deployment configuration, and automated validation.

## Known limitations and future work

- This repository contains deployment configuration, not a credentialed live Render deployment. A Render workspace owner must create/sync the Blueprint and verify its assigned URL.
- Prisma 3, Create React App 5, Cypress 10, and several transitive dependencies are old. Upgrade them deliberately with compatibility testing instead of applying a breaking audit fix blindly.
- The random selection loads at most ten recent rows per score bucket and chooses in application memory; a scalable, statistically verified database-side strategy is future work.
- There is no authentication, rate limiting, moderation, or abuse prevention. Public write endpoints should not be treated as production-hardened.
- The free preview database expires and has no backups. Define retention, backups, monitoring, and a paid production plan before storing important data.
