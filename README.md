# Sing Me A Song

This branch, `eliza-b78ada67/sing-me-a-song`, imports the original `sing-me-a-song` project into `ai-training-workspace-may` and repairs the run path without rewriting the application.

The original Create React App documentation is preserved in `front-end/README.md`. This root README adds the project-specific setup, environment, validation, and deployment guidance that the imported snapshot was missing.

## Project Overview

`Sing Me A Song` is a small full-stack recommendations app. Users submit YouTube music links, browse the latest recommendations, upvote or downvote songs, open a top list, and fetch a random pick.

- `front-end/`: React 18 app built with Create React App, React Router 6, axios, styled-components, and `react-player`
- `back-end/`: Node.js + Express + TypeScript API
- `back-end/prisma/`: PostgreSQL schema and migration history managed by Prisma
- `render.yaml`: simple Render Blueprint for the API, static frontend, and managed PostgreSQL

## Application Flow

1. The React app calls the API URL in `REACT_APP_API_BASE_URL`.
2. Express exposes `/recommendations` routes for create, list, vote, top-N, and random selection.
3. Prisma persists recommendations to PostgreSQL in the `recommendations` table.

Main API routes:

- `POST /recommendations`
- `GET /recommendations`
- `GET /recommendations/random`
- `GET /recommendations/top/:amount`
- `GET /recommendations/:id`
- `POST /recommendations/:id/upvote`
- `POST /recommendations/:id/downvote`
- `GET /health`

When a recommendation drops below score `-5`, the backend deletes it automatically.

## Corrected Setup Instructions

Prerequisites:

- Node.js 18+
- npm
- Docker, or a local/hosted PostgreSQL instance

Local PostgreSQL with Docker:

```bash
docker compose up -d db db-test
```

Backend setup:

```bash
cd back-end
cp .env.example .env
cp .env.test.example .env.test
npm ci
npm run prisma:generate
npm run prisma:migrate
npm run dev
```

Frontend setup in another terminal:

```bash
cd front-end
cp .env.example .env
npm ci
npm start
```

Default local URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5000`
- Health check: `http://localhost:5000/health`

The frontend reads `REACT_APP_API_BASE_URL` at build time. Keep it aligned with the backend URL before running `npm start` or `npm run build`.

## Required Environment Variables

Backend (`back-end/.env`) using the safe values from `back-end/.env.example`:

- `DATABASE_URL`: PostgreSQL connection string used by Prisma
- `PORT`: API port, defaults to `5000`
- `CORS_ORIGIN`: comma-separated browser origins allowed to call the API, for example `http://localhost:3000`
- `MODE`: use `TEST` only when enabling the internal `/tests` reset helper locally

Backend test environment (`back-end/.env.test`) using `back-end/.env.test.example`:

- `PORT=5001`
- `MODE=TEST`
- `CORS_ORIGIN=http://localhost:3000`
- `DATABASE_URL=postgresql://postgres:postgres@localhost:15434/sing_me_a_song_test`

Frontend (`front-end/.env`) using `front-end/.env.example`:

- `REACT_APP_API_BASE_URL`: backend base URL used by axios, for example `http://localhost:5000`

Real `.env` files are git-ignored. Do not commit production URLs with credentials, tokens, passwords, or API keys.

## Validation

Backend build and tests:

```bash
cd back-end
npm run build
npm run test:unit
npm run test:integration
```

Backend integration tests reset the database configured by `back-end/.env.test`, so keep that file pointed at the dedicated test database.

Frontend build:

```bash
cd front-end
npm run build
```

Manual flow check:

1. Start PostgreSQL, backend, and frontend.
2. Create a recommendation on Home.
3. Upvote and downvote it.
4. Open Top and confirm score order updates.
5. Open Random and confirm an empty database shows a clean empty state instead of staying on `Loading...`.

## Deployment Instructions

`render.yaml` defines a simple split deployment on Render:

- managed PostgreSQL database
- Node backend service rooted at `back-end/`
- static frontend service rooted at `front-end/`
- `/health` health check for the backend
- SPA rewrite rule so direct loads of `/top` and `/random` still resolve to `index.html`

Render asks for the host-specific values marked with `sync: false`:

- `CORS_ORIGIN`: the public frontend URL
- `REACT_APP_API_BASE_URL`: the public backend URL

Equivalent manual deployment steps:

1. Provision PostgreSQL and store its connection string in the backend host as `DATABASE_URL`.
2. Deploy `back-end/` as a Node web service.
3. Backend build command: `npm ci && npm run prisma:generate && npm run build`
4. Backend migration command: `npm run prisma:migrate`
5. Backend start command: `npm start`
6. Deploy `front-end/` as a static React site.
7. Frontend build command: `npm ci && npm run build`
8. Set `REACT_APP_API_BASE_URL` on the frontend host to the public backend URL.
9. Set `CORS_ORIGIN` on the backend host to the public frontend URL.

## Fixes Or Improvements Made

- Added a real backend production path: `npm run build` now generates Prisma client code and compiles TypeScript, and `npm start` now launches `dist/server.js`.
- Changed the dev server to build before launch, avoiding fragile `ts-node` ESM startup behavior on modern Node versions.
- Added `dotenv/config` loading in `server.ts` so local `.env` files work when using `npm start`.
- Added configurable CORS through `CORS_ORIGIN`.
- Added `GET /health` for runtime and deployment checks.
- Added route parameter validation so invalid IDs and top-list amounts return `422` instead of bubbling into runtime failures.
- Changed `POST /recommendations` to return the created recommendation body with `201`.
- Capped `top/:amount` queries at 100 rows.
- Fixed broken ESM imports in the test reset path.
- Repaired the backend Jest factory and integration expectations so the unit and integration suites run against deterministic local data.
- Updated `test:integration` to apply migrations to the dedicated test database before running.
- Replaced the unusable frontend API example URL with `http://localhost:5000`.
- Added a development API fallback in axios when `REACT_APP_API_BASE_URL` is absent.
- Fixed the Random page so an empty database renders an empty state and vote actions fetch a fresh random recommendation.
- Added root ignore rules for dependency folders, build output, coverage, and local env files.
- Added safe backend and test env examples.
- Added `docker-compose.yml` for local PostgreSQL and test PostgreSQL.
- Added `render.yaml` and this README so setup and deployment are reproducible.

## Known Limitations Or Future Improvements

- The project still depends on PostgreSQL and has no seeded development data.
- The imported Cypress suite is incomplete and out of sync with the app helpers, so it should be rebuilt around deterministic fixtures before CI relies on it.
- The dependency tree is dated around CRA 5, Prisma 3, and Jest 28 and currently reports audit findings.
- Frontend request failures still use browser `alert()` calls instead of inline error UI.
- The app has no authentication, abuse prevention, or rate limiting.
- Observability is minimal; structured logging and error reporting would make production debugging easier.
