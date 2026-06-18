# Sing Me a Song

Sing Me a Song is a full-stack music recommendation application. Users submit YouTube links, browse the newest or highest-ranked recommendations, ask for a random recommendation, and upvote or downvote entries. A recommendation is deleted automatically when its score falls below `-5`.

This repository preserves the original project in [`front-end`](./front-end) and [`back-end`](./back-end), including the original Create React App documentation in [`front-end/README.md`](./front-end/README.md). The root documentation adds the corrected full-stack setup and deployment workflow.

## Architecture and request flow

- **Frontend:** React 18, React Router, Axios, Styled Components and React Player.
- **Backend:** Express, TypeScript, Joi and Prisma.
- **Database:** PostgreSQL.
- **Container deployment:** Nginx serves the built frontend and proxies `/api/*` to the backend. The backend applies committed Prisma migrations before it starts.

The React API client sends requests to `REACT_APP_API_BASE_URL`. The backend exposes REST routes under `/recommendations` and persists records through Prisma.

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Validate the API and database connection |
| `GET` | `/recommendations` | Return up to 10 newest recommendations |
| `POST` | `/recommendations` | Create a recommendation |
| `GET` | `/recommendations/random` | Return a weighted random recommendation |
| `GET` | `/recommendations/top/:amount` | Return the requested number of highest scores |
| `GET` | `/recommendations/:id` | Return one recommendation |
| `POST` | `/recommendations/:id/upvote` | Increase the score |
| `POST` | `/recommendations/:id/downvote` | Decrease the score, deleting entries below `-5` |

## Prerequisites

- Node.js 16 or later and npm for local development. The frontend container currently builds on Node.js 18; the backend container uses Node.js 16 for compatibility with the original Prisma version.
- PostgreSQL 12 or later for local development, or Docker with Docker Compose for the recommended full-stack workflow.

## Environment variables

Never commit real credentials. The repository ignores `.env` and `.env.*` files while retaining example files.

Backend (`back-end/.env`):

| Name | Required | Example/purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL connection URI; see `back-end/.env.example` |
| `PORT` | No | API port, default `5000` |
| `MODE` | No | Use `DEV` locally. Test-only reset routes are enabled only when set to `TEST`. |

Frontend (`front-end/.env`):

| Name | Required | Example/purpose |
| --- | --- | --- |
| `REACT_APP_API_BASE_URL` | Recommended | API origin, such as `http://localhost:5000`; defaults to that value for local development |

Docker Compose (root `.env`):

Copy `.env.docker.example` to `.env`, replace the database-password placeholder with a local-only password, and change published ports if they conflict with other processes. PostgreSQL is published only on the loopback interface at `POSTGRES_PORT` (default `5433`) so the test runner can reach it without making it externally accessible.

## Recommended setup: Docker Compose

```bash
cp .env.docker.example .env
# Edit .env and replace POSTGRES_PASSWORD before continuing.
docker compose up --build -d
```

Open `http://localhost:8080` (or the configured `FRONTEND_PORT`). The API is also published on `http://localhost:5000`; `curl http://localhost:5000/health` should return `{"status":"ok"}`. The named `postgres_data` volume preserves database records across restarts.

To stop the app:

```bash
docker compose down
```

`docker compose down -v` also deletes the database volume and should be used only when a complete local reset is intended.

## Local setup without Docker

Create a PostgreSQL database, then configure and start the backend:

```bash
cd back-end
npm ci
cp .env.example .env
# Edit DATABASE_URL in .env.
npx prisma migrate deploy
npm run dev
```

In another terminal, configure and start the frontend:

```bash
cd front-end
npm ci
cp .env.example .env
# Set REACT_APP_API_BASE_URL=http://localhost:5000
npm start
```

## Validation

Backend unit tests do not need a database. Integration tests require a separate PostgreSQL test database and `back-end/.env.test` containing `DATABASE_URL` and `MODE=TEST`.

```bash
# Backend
cd back-end
npm run typecheck
npm run build
npm run test:unit

# Full backend suite (destructively resets the configured test database)
cp .env.example .env.test
# Point DATABASE_URL at a disposable test database and set MODE=TEST.
npm test

# Frontend
cd front-end
CI=true npm test -- --watchAll=false
npm run build
```

Do not point `.env.test` at a development or production database: `npm test` resets the configured schema.

## Production deployment

The included Docker Compose topology is the reference deployment and can run on any Linux host with Docker Compose:

1. Clone the requested branch and create the root `.env` from `.env.docker.example`.
2. Set a strong, unique PostgreSQL password and firewall ports so only the frontend is publicly exposed unless direct API access is required.
3. Run `docker compose up --build -d`.
4. Terminate TLS at the host's ingress/reverse proxy and forward it to the configured frontend port.
5. Confirm `/api/health` through the public frontend origin and exercise create, list, vote, top and random flows.

For a split-platform deployment, build `back-end/Dockerfile`, provide `DATABASE_URL` through the host's secret store, and use `npm start` as the API command. Build the React app with `REACT_APP_API_BASE_URL` set to the public API URL, or retain the supplied Nginx proxy when the services share a Docker network.

## Repairs and improvements in this branch

- Corrected the backend production entry point, added production compilation/migration scripts, and removed an unused backend-only React dependency.
- Repaired the Prisma import that prevented Jest and the API from loading reliably with the ESM configuration.
- Added positive-integer route parameter validation, stable JSON error responses, a database-backed health endpoint, and graceful Prisma disconnection on shutdown.
- Fixed broken ESM imports in test-only routes and replaced an undeclared CommonJS test dependency with deterministic Faker data.
- Fixed unit tests that did not await rejected promises and allowed real database calls to escape mocks.
- Made frontend async actions reject on API errors so failed writes no longer look successful or trigger unsafe refreshes.
- Added explicit API failure and empty-random states, and made Random recover when the current recommendation was removed by a downvote.
- Added frontend API-route tests and removed the production-build lint warning.
- Added safe environment templates and an end-to-end containerized deployment with PostgreSQL health gating and automatic Prisma migrations.

## Known limitations and suggested next work

- The original dependency baseline (Create React App, Prisma 3, Jest 28 and Node.js 16-compatible backend tooling) is old. Upgrade these in a separate focused change with migration and regression testing.
- The API has no authentication, rate limiting or write-abuse controls; it should not be exposed to untrusted traffic without ingress-level safeguards.
- Names are globally unique but normalization is minimal; visually equivalent names can still be created with whitespace or casing differences.
- Browser-level Cypress tests are retained from the original project but are not wired into a deterministic CI environment.
- The test suite expects a separately configured PostgreSQL instance. A disposable CI service container would make integration testing repeatable.
