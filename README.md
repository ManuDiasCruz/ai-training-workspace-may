# Sing Me a Song

Sing Me a Song is a full-stack music recommendation app. Users can submit YouTube songs, browse recent recommendations, upvote or downvote songs, see the top ranked songs, and open a random recommendation.

The app is split into:

- `front-end/`: React 18 app created with Create React App.
- `back-end/`: Express, TypeScript, Prisma, and PostgreSQL API.

The original Create React App documentation is preserved in `front-end/README.md`.

## Requirements

- Node.js 20 or compatible LTS version.
- npm.
- PostgreSQL.

## Environment Variables

Backend variables are documented in `back-end/.env.example`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
PORT=5000
CORS_ORIGIN=http://localhost:3000
```

Test variables are documented in `back-end/.env.test.example`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/TEST_DATABASE
MODE=TEST
```

Frontend variables are documented in `front-end/.env.example`:

```env
REACT_APP_API_BASE_URL=http://localhost:5000
```

Do not commit real `.env` files or private credentials.

## Local Setup

Install dependencies:

```bash
npm install --prefix back-end
npm install --prefix front-end
```

Create PostgreSQL databases for development and tests, then create local env files from the examples:

```bash
cp back-end/.env.example back-end/.env
cp back-end/.env.test.example back-end/.env.test
cp front-end/.env.example front-end/.env
```

Apply database migrations:

```bash
npm --prefix back-end run migrate:dev
```

Start the backend:

```bash
npm --prefix back-end run dev
```

Start the frontend in another terminal:

```bash
npm --prefix front-end start
```

Open `http://localhost:3000`.

## Tests and Builds

Backend tests reset the configured test database before running:

```bash
npm --prefix back-end test
```

Production builds:

```bash
npm --prefix back-end run build
npm --prefix front-end run build
```

## Deployment

This branch includes `render.yaml` for a simple Render Blueprint deployment. The blueprint creates:

- one Node web service that builds the frontend and backend,
- one Render Postgres database,
- a pre-deploy migration step,
- `/health` for service health checks.

The deployed Express app serves the React production build in `NODE_ENV=production`, so the frontend can call the API with same-origin relative requests.

High-level Render steps:

1. Push this branch to GitHub.
2. In Render, create a new Blueprint from this repository and select this branch.
3. Render reads `render.yaml`, provisions the web service and database, injects `DATABASE_URL`, runs migrations, and starts the app.
4. Verify `https://<service>.onrender.com/health` returns `200 OK`.
5. Open the service URL and create/upvote/list recommendations.

Render's Blueprint reference documents `render.yaml`, `buildCommand`, `preDeployCommand`, `startCommand`, `staticPublishPath`, database `fromDatabase` references, and `sync: false` secret handling.

## Fixes and Improvements Made

- Imported the public `sing-me-a-song` app onto this branch.
- Added safe backend and test env examples.
- Fixed backend production scripts and TypeScript build output.
- Fixed Prisma test reset for non-interactive environments.
- Fixed backend create route to return the created recommendation.
- Added validation for numeric route parameters.
- Made top recommendation ordering deterministic.
- Fixed ESM import issues that broke compiled backend startup.
- Added configurable CORS and `/health`.
- Fixed frontend API fallback, local proxy, document title, and build warning.
- Repaired backend factories/tests so unit and integration tests pass.

## Known Limitations and Future Improvements

- Dependencies are old and `npm audit` reports vulnerabilities; upgrading React Scripts, Prisma, Jest, and related packages should be done in a focused pass.
- Cypress specs from the original project are incomplete and should be replaced with reliable app-level E2E tests.
- The UI uses alert-based error handling and could provide inline form and network feedback.
- Recommendation deletion after repeated downvotes is backend-only; the frontend can improve the deleted-item refresh state.
