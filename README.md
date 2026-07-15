# Sing me a Song

Sing me a Song is a full-stack song recommendation app. People can submit a YouTube song, browse the newest recommendations, vote them up or down, view the top ten, and ask for a weighted random recommendation. Recommendations are removed automatically after their score drops below `-5`.

The original Create React App notes are preserved in [`front-end/README.md`](front-end/README.md).

## Application flow

1. The React client calls the Express API under `/recommendations`.
2. Express validates request bodies and route parameters, then delegates to the service and repository layers.
3. Prisma persists recommendations in PostgreSQL.
4. In production, Express also serves the compiled React app, so browser and API requests share one origin.

## Project structure

```text
back-end/                 Express, TypeScript, Prisma, Jest, and API tests
  prisma/                 PostgreSQL schema and migrations
  src/                    Routes, controllers, services, and repositories
front-end/                React, styled-components, and Cypress
  cypress/e2e/app.cy.js   Main browser-flow coverage
  src/                    Pages, components, hooks, and API client
render.yaml               Render web service and PostgreSQL Blueprint
```

## Prerequisites

- Node.js `22.x` (the deployment uses `22.22.0`)
- npm
- PostgreSQL

## Local setup

1. Install both applications:

   ```bash
   npm run install:all
   ```

2. Create local development and test databases in PostgreSQL:

   ```sql
   CREATE DATABASE sing_me_a_song;
   CREATE DATABASE sing_me_a_song_test;
   ```

3. Copy `back-end/.env.example` to `back-end/.env` and set the local connection string. Copy `back-end/.env.test.example` to `back-end/.env.test` for integration and E2E tests. Copy `front-end/.env.example` to `front-end/.env` when the API is not running on `http://localhost:5000`.

4. Apply the development migration:

   ```bash
   npm run db:migrate
   ```

5. Start the API and web client in separate terminals:

   ```bash
   npm run dev:api
   npm run dev:web
   ```

   The client runs at `http://localhost:3000`; the API defaults to `http://localhost:5000`.

## Environment variables

| File / runtime | Variable | Required | Purpose |
| --- | --- | --- | --- |
| Backend | `DATABASE_URL` | Yes | PostgreSQL connection string used by Prisma. |
| Backend | `PORT` | No | API port; defaults to `5000` locally and is supplied by Render in production. |
| Backend | `CORS_ORIGIN` | No | Comma-separated allowed browser origins for split local deployments. If unset, CORS accepts browser origins. |
| Backend test | `MODE=TEST` | For E2E reset route | Enables `DELETE /tests/reset`; never enable this in production. |
| Frontend build | `REACT_APP_API_BASE_URL` | No | API origin. Defaults to `http://localhost:5000` in development and same-origin in production. |
| Cypress | `CYPRESS_BASE_URL` | No | Client URL; defaults to `http://localhost:3000`. |
| Cypress | `CYPRESS_API_URL` | No | API URL; defaults to `http://localhost:5000`. |

Do not commit `.env`, `.env.test`, database passwords, tokens, or private connection strings. The repository tracks examples only.

## Commands

```bash
npm test                 # deterministic backend unit suite
npm run test:integration # API + PostgreSQL integration suite
npm run test:e2e         # Cypress main browser flows; API must run with MODE=TEST
npm run build            # Prisma/TypeScript build and optimized React build
npm start                # serve the API and compiled React app
```

For an E2E run, start the backend with the test environment and the frontend in separate terminals, then run `npm run test:e2e`.

## API routes

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Deployment health check. |
| `GET` | `/recommendations` | Latest ten recommendations. |
| `POST` | `/recommendations` | Create a validated YouTube recommendation. |
| `GET` | `/recommendations/:id` | Get one recommendation. |
| `POST` | `/recommendations/:id/upvote` | Increase a score. |
| `POST` | `/recommendations/:id/downvote` | Decrease a score and remove scores below `-5`. |
| `GET` | `/recommendations/top/:amount` | Highest-scoring recommendations (`1` to `100`). |
| `GET` | `/recommendations/random` | Weighted random recommendation. |

## Deployment

The included Render Blueprint provisions one Node web service and one PostgreSQL database:

1. Push the branch to GitHub.
2. In Render, create a new Blueprint from this repository and select `cy-eh-sing-me-a-song`.
3. Confirm `render.yaml`. Render installs both lockfiles, builds both applications, applies `prisma migrate deploy`, and starts the combined server.
4. Verify `/health`, create/vote/list flows, `/top`, and `/random` on the assigned `onrender.com` URL.

The Blueprint uses Render's free instances for demonstration. Free web services spin down after 15 minutes without traffic and can take about a minute to wake. Free PostgreSQL databases expire after 30 days and have no backups; upgrade the database before that deadline for persistent use.

## Repairs and improvements

- Corrected the backend production build/start path and ESM import failures.
- Added environment loading, graceful shutdown, a health endpoint, safe 404s, static React serving, and configurable CORS.
- Added request validation for recommendation IDs, top amounts, names, and YouTube URLs.
- Return the created recommendation from `POST /recommendations`.
- Fixed frontend API defaults, async error handling, retry states, nested routes, duplicate voting, and random-item refresh behavior.
- Replaced nondeterministic and broken test fixtures with deterministic unit and Cypress coverage.
- Added safe environment examples, root commands, a pinned Node version, and an infrastructure-as-code deployment.

## Known limitations and future improvements

- Create React App, Prisma 3, Jest 28, Cypress 10, and several transitive packages are dated; upgrade them in a dedicated compatibility change.
- Add continuous integration with a disposable PostgreSQL service to run build, unit, integration, and Cypress checks on every pull request.
- The free Render database expires after 30 days; use a persistent paid database and add backups/monitoring for ongoing production use.
- The app has no authentication or rate limiting, so public submissions and votes are intentionally open.
- Playback depends on YouTube embed availability and the owner allowing third-party embedding.
