# Sing Me a Song

Sing Me a Song is a full-stack music recommendation app. People can submit YouTube songs, browse the latest or highest-scoring recommendations, receive a weighted random recommendation, and upvote or downvote songs. A recommendation is removed after its score drops below `-5`.

This repaired version keeps the original React, Express, Prisma, and PostgreSQL architecture. The original Create React App documentation is preserved in [`front-end/README.md`](front-end/README.md).

## Project structure and flow

- `front-end/` contains the React 18 single-page application.
- `back-end/` contains the Express API, service/repository layers, Prisma schema, migrations, and tests.
- `render.yaml` describes a single Render web service plus PostgreSQL database. In production, Express serves the compiled frontend and the API from one origin.
- A frontend action calls the recommendation service, Axios sends the request to Express, the controller validates it, the service applies recommendation rules, and the repository persists it through Prisma.

The main API routes are:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Verify that the server and database are reachable |
| `GET` | `/recommendations` | Return the 10 newest recommendations |
| `POST` | `/recommendations` | Create a recommendation |
| `GET` | `/recommendations/top/:amount` | Return up to 100 recommendations ordered by score |
| `GET` | `/recommendations/random` | Return one weighted random recommendation |
| `GET` | `/recommendations/:id` | Return one recommendation |
| `POST` | `/recommendations/:id/upvote` | Increment a score |
| `POST` | `/recommendations/:id/downvote` | Decrement a score and remove scores below `-5` |

## Requirements

- Node.js 22 (see `.nvmrc`)
- npm
- PostgreSQL 13 or newer

No credentials are committed. Local `.env` files are ignored by Git; use the checked-in examples as templates.

## Local setup

1. Create local databases named `sing_me_a_song` and `sing_me_a_song_test`.
2. Copy `back-end/.env.example` to `back-end/.env` and adjust the PostgreSQL URL if needed.
3. Copy `back-end/.env.test.example` to `back-end/.env.test` and keep it pointed at the dedicated test database.
4. Install dependencies and apply the development migration:

   ```bash
   npm --prefix back-end ci
   npm --prefix front-end ci
   npm --prefix back-end run db:migrate
   ```

5. In separate terminals, start both applications:

   ```bash
   npm --prefix back-end run dev
   npm --prefix front-end start
   ```

6. Open `http://localhost:3000`. The frontend defaults to the API at `http://localhost:5000` in development.

### Environment variables

| Variable | Location | Required | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | backend | Yes | PostgreSQL connection URL used by Prisma |
| `PORT` | backend | No | Express port; defaults to `5000` locally and is assigned by Render |
| `CORS_ORIGIN` | backend | No | Comma-separated allowed browser origins; all origins are accepted when unset |
| `MODE` | backend | Tests only | Set to `TEST` to expose the database reset route used by Cypress |
| `NODE_ENV` | backend | Production | Enables serving `front-end/build` from Express |
| `REACT_APP_API_BASE_URL` | frontend | No | API URL override; defaults to port `5000` in development and same-origin in production |

## Validation and tests

Run the database-free checks with:

```bash
npm --prefix back-end test
npm --prefix back-end run build
CI=true npm --prefix front-end test -- --watchAll=false
npm --prefix front-end run build
```

Run backend integration tests only against the dedicated test database:

```bash
npm --prefix back-end run db:reset:test
npm --prefix back-end run test:integration
```

For the Cypress main-flow smoke test, start the backend with `MODE=TEST`, start the frontend, then run:

```bash
npm --prefix front-end exec cypress run
```

The smoke spec creates a song, verifies the API response, upvotes it, and checks the Home, Top, and Random views.

## Production build

Build both applications, apply migrations, and start Express:

```bash
npm --prefix back-end ci
npm --prefix back-end run build
npm --prefix front-end ci
npm --prefix front-end run build
npm --prefix back-end run db:migrate
NODE_ENV=production npm --prefix back-end start
```

Express serves the SPA and API together. `GET /health` performs a small database query, so a healthy response proves the deployed service can reach PostgreSQL.

## Render deployment

1. Push this repository and select the `0827-yahk2-singasong` branch in Render.
2. In the Render dashboard, create a Blueprint from the repository's `render.yaml`.
3. Review the free web service and free PostgreSQL resources, then apply the Blueprint.
4. Render injects `DATABASE_URL`; no database password needs to be copied into GitHub or the repository.
5. On startup, the service runs `prisma migrate deploy`, starts Express, and checks `/health` before accepting traffic.

The free Render web service can sleep after 15 minutes of inactivity. Its first request after sleeping may take about a minute. A free Render PostgreSQL database expires after 30 days and has no backups, so upgrade or move the database before using this as a durable production service. See the [Render free-tier documentation](https://render.com/docs/free).

## Fixes and improvements made

- Corrected the backend production entry point and added explicit build, migration, development, and cross-platform test scripts.
- Upgraded Prisma to a modern PostgreSQL/Node-compatible release and removed backend runtime audit findings.
- Added safe environment examples, Node version guidance, graceful shutdown, database-aware health checks, and production SPA hosting.
- Fixed missing ESM import extensions in test-only routes and removed an undeclared test dependency.
- Corrected broken integration-test assumptions and restored the unit suite.
- Added request-body and route-parameter validation, bounded top-list amounts, and unique-conflict handling.
- Added API timeouts, same-origin production requests, actionable frontend failure states, and accessible vote/form controls.
- Kept form values after failed submissions and fixed Random view behavior for empty/deleted recommendations.
- Patched direct Axios/React Router dependencies, upgraded Cypress, and added focused frontend unit and end-to-end smoke coverage.
- Added a reproducible Render Blueprint for a combined frontend/backend deployment with managed PostgreSQL.

## Known limitations and future improvements

- Create React App is deprecated and its transitive build/test toolchain still reports npm advisories. Migrating to Vite and React Router 7 should be handled as a focused follow-up rather than mixed into this repair.
- Database integration and Cypress tests require PostgreSQL and are intentionally separated from the fast unit/build checks. CI should provision PostgreSQL and run them automatically.
- The free Render database is temporary (30 days) and has no backups. A durable environment needs a paid or external managed PostgreSQL plan with backups.
- Recommendation feeds return at most 10 records and do not expose pagination.
