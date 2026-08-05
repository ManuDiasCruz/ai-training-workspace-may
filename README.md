# Sing Me a Song

Sing Me a Song is a small full-stack music recommendation app. Users submit a name and an HTTPS YouTube link, browse the ten newest recommendations, upvote or downvote them, view the top ten by score, and ask for a weighted random recommendation. A recommendation is removed after its score drops below -5.

This branch imports the original [`sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song) project into [`ai-training-workspace-may`](https://github.com/ManuDiasCruz/ai-training-workspace-may). The original Create React App documentation remains in [`front-end/README.md`](front-end/README.md).

## Project layout and flow

| Directory | Responsibility |
| --- | --- |
| `front-end/` | React 18, React Router, Axios, styled-components, React Player, and Cypress smoke tests |
| `back-end/` | Express API, Joi validation, Prisma repository/service layer, Jest unit and integration tests |
| `back-end/prisma/` | PostgreSQL schema and versioned migration |

The browser calls `/recommendations`. The controller validates input and route parameters, the service applies uniqueness/voting/random rules, and Prisma persists the `Recommendation` model in PostgreSQL. In local development the React server calls the API on port 5000. The supplied production configuration builds the React app and lets Express serve it from the same origin, avoiding a separate frontend/API CORS or build-time URL coupling.

## Prerequisites

- Node.js 20.x (`.node-version` pins the deployment family) and npm
- PostgreSQL 13+ with two separate databases: one for development and one disposable database for tests
- A browser for the UI; Cypress also requires its platform browser dependencies

## Local setup

1. Create PostgreSQL databases, for example `sing_me_a_song` and `sing_me_a_song_test`.
2. Copy `back-end/.env.example` to `back-end/.env`, and replace the placeholder user/password/database with your local development connection string.
3. Copy `back-end/.env.test.example` to `back-end/.env.test`, and point it at the **separate disposable test database**. `npm test` resets this database.
4. Copy `front-end/.env.example` to `front-end/.env` for separate local servers.
5. Install and migrate:

```bash
cd back-end
npm ci
npm run migrate:deploy
npm run dev
```

In another terminal:

```bash
cd front-end
npm ci
npm start
```

Open `http://localhost:3000`. The API listens on `http://localhost:5000` by default. `GET /health` returns `{ "status": "ok" }`.

### Environment variables

| Variable | Location | Required | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | backend | Yes | PostgreSQL Prisma connection string. Never commit a real value. |
| `PORT` | backend | No | HTTP port; defaults to 5000 locally and is supplied by a host in production. |
| `CORS_ORIGIN` | backend | Separate-origin UI only | Comma-separated allowed browser origins, such as `http://localhost:3000`. Omit for same-origin hosting. |
| `MODE` | backend test only | Test server | Set `TEST` only in `.env.test` to expose `DELETE /tests/reset`. Never set it in production. |
| `SERVE_FRONTEND` | backend | No | Set `true` to serve `front-end/build` and React Router deep links from Express. |
| `REACT_APP_API_BASE_URL` | frontend build | Separate-origin UI only | API origin. Local example is `http://localhost:5000`; leave unset for the supplied same-origin production build. CRA embeds `REACT_APP_*` values in the public bundle, so never put secrets there. |

Both application `.gitignore` files exclude `.env` values while allowing the safe examples. Do not commit tokens, passwords, database URLs with real credentials, or hosting secrets.

## Validation

```bash
cd back-end
npm run build
npm test
```

`npm test` force-resets only the database selected by `.env.test`, then runs unit and PostgreSQL-backed integration tests. Check that connection string before running it.

```bash
cd front-end
npm run build
```

For end-to-end tests, start the backend in test mode and the frontend in separate terminals:

```bash
cd back-end && npm run dev:test
cd front-end && npm start
cd front-end && npm run test:e2e
```

The focused Cypress suite resets `/tests/reset`, creates a recommendation, votes, navigates through Top and Random, checks the empty random state, and checks duplicate-name feedback. Override `baseUrl` or `apiUrl` through Cypress configuration/environment if your local ports differ.

## API summary

| Method | Route | Result |
| --- | --- | --- |
| `GET` | `/health` | Process liveness |
| `POST` | `/recommendations` | Validate and create; returns the created record with status 201 |
| `GET` | `/recommendations` | Ten newest records, newest first |
| `GET` | `/recommendations/random` | Weighted random recommendation or 404 when empty |
| `GET` | `/recommendations/top/:amount` | Up to 100 records, score descending with deterministic ID tie-break |
| `GET` | `/recommendations/:id` | One record or 404 |
| `POST` | `/recommendations/:id/upvote` | Increment score |
| `POST` | `/recommendations/:id/downvote` | Decrement; remove below -5 |
| `DELETE` | `/tests/reset` | Test-mode-only database reset |

Invalid bodies and positive-integer parameters return 422; duplicate names return 409; missing records return 404. Unexpected errors return a generic JSON 500 response without exposing internals.

## Deployment (Render Blueprint)

[`render.yaml`](render.yaml) defines a single Node web service and a managed PostgreSQL database in the same region. The web service builds both packages, runs Prisma's idempotent `migrate deploy` before starting, serves the React build from Express, and uses `/health` for the host check. `DATABASE_URL` is wired from the database resource without a credential in Git.

1. Push `731-d-h-singmeasong` to GitHub.
2. In Render, create a Blueprint from `ManuDiasCruz/ai-training-workspace-may` and select this branch. Review the proposed resources and costs before applying.
3. Wait for the database and web service deploy to succeed. Do **not** set `MODE=TEST` in the service.
4. Open the service's `onrender.com` URL and verify `/health`, the home page, creating an HTTPS YouTube recommendation, upvoting, Top, Random, and a direct `/top` refresh.
5. Inspect service logs if migration or startup fails; confirm `DATABASE_URL` is the internal connection string and both resources are in the same region.

The Blueprint uses free instance types for a preview/hobby deployment. Render's free web service spins down after inactivity, and its free PostgreSQL database expires after 30 days and has no backups. Upgrade to appropriate paid instances and backup/monitoring policies before using this for durable production data. See [Render's free-instance limitations](https://render.com/docs/free) and [Blueprint reference](https://render.com/docs/blueprint-spec).

For another host, run `npm ci` and `npm run build` in each package, provide a managed `DATABASE_URL`, run `npm run migrate:deploy` from `back-end`, set `SERVE_FRONTEND=true`, and start `back-end/dist/server.js` with the host-provided `PORT`. If frontend and API are hosted separately, build the frontend with its public API origin and set `CORS_ORIGIN` to the exact frontend origin.

## Repairs in this branch

- Corrected the backend build output and production start entry point; added dotenv loading and graceful shutdown.
- Added safe development/test environment examples and cross-platform test scripts.
- Repaired ESM test-mode imports and removed the undeclared CommonJS random-video dependency from test factories.
- Returned created records, validated numeric route parameters and playable HTTPS YouTube URLs, handled Prisma uniqueness/not-found races, and made top-score ties deterministic.
- Added a health route, explicit JSON 404/500 responses, configurable CORS, and same-origin SPA serving with deep-link fallback.
- Repaired frontend API defaults, request error propagation, retry/empty states, form retention on failure, and accessible disabled vote controls.
- Replaced imported Cypress tutorial/stale specs with a focused application smoke suite and corrected the test reset URL.
- Added a Render Blueprint and deployment/runbook documentation.

## Known limitations and future work

- The Render Blueprint is deployment-ready but requires an authorized Render account/workspace to provision. A live URL cannot be claimed until that deployment is applied and verified.
- The legacy Create React App and Prisma 3 dependency trees have audit findings and aging tooling. Plan controlled upgrades with regression tests rather than `npm audit fix --force`.
- Random selection currently samples the repository's limited candidate lists; a database-side weighted/random strategy would scale better.
- Voting is anonymous and unrestricted. A public deployment should add rate limiting, abuse controls, and an authentication/ownership policy appropriate to the product.
- `/health` is liveness only. Add a separate database readiness probe and monitoring/alerting for production.
- Cypress requires a supported browser environment. If browser execution is unavailable, backend integration and production HTTP smoke tests still validate the API, but they do not replace interactive UI QA.
