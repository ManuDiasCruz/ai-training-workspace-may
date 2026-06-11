# Sing Me A Song

Sing Me A Song is a full-stack music recommendation application. Users can submit YouTube songs, browse recent recommendations, vote songs up or down, view the top-ranked list, and request a weighted random recommendation.

The original Create React App documentation is preserved in `front-end/README.md`. This root README adds project-specific setup, validation, and deployment guidance.

## Project Overview

- `back-end/`: Express, TypeScript, Prisma, and PostgreSQL REST API.
- `front-end/`: React single-page application.
- `back-end/prisma/`: database schema and migration history.
- `docker-compose.yml`: production-style local deployment with PostgreSQL, the compiled API, nginx, and the built React application.
- `render.yaml`: optional Render Blueprint for public hosting.

## Application Flow

- `POST /recommendations`: create and return a recommendation.
- `GET /recommendations`: list the latest 10 recommendations.
- `GET /recommendations/:id`: fetch one recommendation.
- `POST /recommendations/:id/upvote`: increment its score.
- `POST /recommendations/:id/downvote`: decrement its score and remove it below `-5`.
- `GET /recommendations/top/:amount`: list recommendations by score.
- `GET /recommendations/random`: return a weighted random recommendation.
- `GET /health`: deployment health check.

## Prerequisites

- Node.js 20
- npm
- Docker with Docker Compose, or a reachable PostgreSQL server

Use `nvm use` from the repository root when nvm is installed.

## Local Setup

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Configure and start the backend:

```bash
cd back-end
cp .env.example .env
cp .env.test.example .env.test
npm ci
npx prisma migrate deploy
npm run dev
```

Configure and start the frontend in another terminal:

```bash
cd front-end
cp .env.example .env
npm ci
npm start
```

Default development URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5000`
- Health check: `http://localhost:5000/health`

## Environment Variables

Backend `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/sing_me_a_song
PORT=5000
CORS_ORIGIN=http://localhost:3000,http://localhost:8080
MODE=DEV
```

Backend `.env.test` uses the same fields with the `sing_me_a_song_test` database and `MODE=TEST`.

Frontend `.env`:

```env
REACT_APP_API_BASE_URL=http://localhost:5000
```

The root `.env` can override Compose ports and the frontend build-time API URL. Real environment files are ignored; only safe examples are committed.

## Validation

Backend:

```bash
cd back-end
npm test
npm run build
```

Frontend:

```bash
cd front-end
CI=true npm run build
```

Deployed browser smoke:

```bash
cd front-end
CYPRESS_BASE_URL=http://localhost:8080 npx cypress run --spec cypress/e2e/app/smoke.cy.js
```

## Docker Deployment

Copy the root Compose example when custom ports are needed, then build and start the production stack:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Default deployment URLs:

- Application: `http://localhost:8080`
- API: `http://localhost:5000`
- PostgreSQL: `localhost:5433`

The frontend nginx service proxies `/api/*` to the backend, so browser requests use the same origin. The backend container applies pending Prisma migrations before starting.

Stop the deployment with:

```bash
docker compose down
```

## Public Deployment

`render.yaml` defines a Render Postgres database, Node API service, and static React site. Connect this repository as a Render Blueprint, then provide these prompted values in the dashboard:

- API `CORS_ORIGIN`: the public frontend URL.
- Frontend `REACT_APP_API_BASE_URL`: the public API URL.

Render builds the backend, runs Prisma migrations as a pre-deploy command, checks `/health`, builds the frontend, and rewrites SPA routes to `index.html`. An authenticated Render workspace is required; no hosting credentials are stored in this repository.

## Fixes And Improvements

- Repaired Node 20/22 development startup by replacing the broken ts-node/nodemon ESM path with `tsx`.
- Added a real backend build and corrected production startup to `dist/server.js`.
- Added dotenv loading and Prisma CommonJS/ESM interoperability.
- Added configurable CORS, a health endpoint, and positive-integer route validation.
- Made recommendation creation return the created row.
- Removed an unused backend React dependency and macOS metadata files from source control.
- Repaired ESM imports in the test reset flow and removed a missing YouTube fixture dependency.
- Replaced the deadlocking legacy unit file with deterministic service tests and corrected integration assertions.
- Fixed the frontend API URL template and production fallback.
- Fixed the Random page empty state and refresh-after-vote behavior.
- Added a focused Cypress deployment smoke test.
- Added safe environment templates, Docker deployment files, and a current Render Blueprint.
- Fixed Prisma 3 container builds by installing OpenSSL before client generation.

## Known Limitations And Future Improvements

- The legacy CRA 5, Prisma 3, Jest 28, and Cypress 10 dependency trees report npm audit findings and should be upgraded in a dedicated change.
- Several imported Cypress scaffold/example specs are intentionally excluded from the maintained smoke suite.
- Frontend request failures still rely on browser alerts in some flows.
- The application has no authentication, moderation, rate limiting, or abuse prevention.
- Logging and production observability are minimal.
- Free hosting plans can sleep, expire, or introduce cold starts depending on provider policy.
