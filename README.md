# Sing Me A Song

This branch brings the `sing-me-a-song` full-stack project into `ai-training-workspace-may` and keeps the original Create React App notes in `front-end/README.md`.

## Project Overview

`Sing Me A Song` lets users create YouTube music recommendations, view the latest recommendations, vote them up or down, open a top list, and get a random recommendation.

- `back-end/`: Express + TypeScript + Prisma API
- `front-end/`: Create React App client
- `back-end/prisma/`: PostgreSQL schema and migrations

## Corrected Setup Instructions

Prerequisites:

- Node.js 22+
- npm
- Docker, or PostgreSQL 15+ available locally or through a hosted provider

Local database with Docker:

```bash
docker compose up -d db
```

Backend setup:

```bash
cd back-end
npm ci
cp .env.example .env
npm run prisma:generate
npm run prisma:migrate
npm run dev
```

Frontend setup in another terminal:

```bash
cd front-end
npm ci
cp .env.example .env
npm start
```

Default local URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5000`
- Health check: `http://localhost:5000/health`

## Required Environment Variables

Backend (`back-end/.env`):

- `PORT`: API port. Defaults to `5000`.
- `MODE`: use `TEST` only when enabling the internal test reset route.
- `CORS_ORIGIN`: comma-separated browser origins allowed to call the API. Example: `http://localhost:3000`
- `DATABASE_URL`: PostgreSQL connection string. Never commit a real production value.

Frontend (`front-end/.env`):

- `REACT_APP_API_BASE_URL`: backend base URL used by Axios. Example: `http://localhost:5000`

Safe example values live in `back-end/.env.example` and `front-end/.env.example`.

## Deployment Instructions

A simple deployment path is:

1. Provision a PostgreSQL database and copy its connection string into the backend host as `DATABASE_URL`.
2. Deploy `back-end/` as a Node web service.
3. Backend build command: `npm ci && npm run prisma:generate && npm run build`
4. Backend start command: `npm run prisma:migrate && npm start`
5. Deploy `front-end/` as a static React site.
6. Frontend build command: `npm ci && npm run build`
7. Set `REACT_APP_API_BASE_URL` on the frontend host to the public backend URL.
8. Set `CORS_ORIGIN` on the backend host to the public frontend URL.

The same split works on common hosting combinations such as a static frontend host plus a Node backend host backed by managed PostgreSQL.

## Fixes Or Improvements Made

- Restored runnable backend scripts for current Node versions by compiling with `tsc` before execution.
- Corrected the production start path from `dist/index.js` to the built server entrypoint.
- Fixed two broken ESM imports in the test reset path that prevented compiled backend startup.
- Added a `/health` endpoint for runtime and deployment verification.
- Added numeric route validation so invalid IDs and top-list amounts return a controlled `422` instead of causing runtime failures.
- Replaced the broken frontend API example URL with `http://localhost:5000`.
- Added a frontend Axios fallback to the local backend URL so the app is usable during local setup.
- Added `.gitignore` coverage for dependencies, builds, local env files, and generated runtime artifacts.
- Added safe backend env examples and deployment guidance.

## Known Limitations Or Future Improvements

- The project still depends on PostgreSQL and has no seeded development data yet.
- The dependency tree is from an older CRA/Prisma stack and currently reports npm audit findings.
- Frontend UX still uses browser alerts for failed actions and has limited empty/error state handling on the random recommendation page.
- Browser routing on static hosts may need a rewrite rule so `/top` and `/random` resolve to `index.html`.
