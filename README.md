# Sing Me a Song 🎵

A full-stack song-recommendation app. Users submit YouTube songs, up/down‑vote
them, and browse a timeline, a top-ranked list, or a score-weighted random pick.

> This branch (`claude-b78ada67/sing-me-a-song`) of the
> **ai-training-workspace-may** repo imports the original
> [sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song) project and
> repairs it so it runs on modern Node, builds for production, and deploys with a
> single command. See [Fixes & improvements](#fixes--improvements-made) below.

---

## Project overview

| Layer    | Tech                                                              |
| -------- | ---------------------------------------------------------------- |
| Frontend | React 18 (Create React App), React Router 6, styled-components, axios, react-player |
| Backend  | Node.js + Express 4, TypeScript (ESM), Joi validation             |
| Database | PostgreSQL via Prisma ORM                                         |
| Tests    | Jest + Supertest (back-end), Cypress (front-end E2E)             |
| Deploy   | Docker + Docker Compose (Postgres + API + nginx)                |

### Application flow

1. The React app calls the API base URL in `REACT_APP_API_BASE_URL`.
2. The Express API exposes `/recommendations` for creating, listing, voting,
   top-N and random selection. A recommendation dropping below `-5` score is
   automatically removed.
3. Prisma persists recommendations to PostgreSQL (`recommendations` table).

```
React (nginx) ──HTTP──▶ Express API ──Prisma──▶ PostgreSQL
```

### API reference

| Method | Route                          | Description                              |
| ------ | ------------------------------ | ---------------------------------------- |
| POST   | `/recommendations`             | Create a recommendation (`name`, `youtubeLink`) |
| GET    | `/recommendations`             | List the 10 most recent                  |
| GET    | `/recommendations/random`      | Score-weighted random recommendation     |
| GET    | `/recommendations/top/:amount` | Top `amount` by score                    |
| GET    | `/recommendations/:id`         | Get one by id                            |
| POST   | `/recommendations/:id/upvote`  | +1 score                                 |
| POST   | `/recommendations/:id/downvote`| -1 score (auto-deletes below -5)         |
| DELETE | `/tests/reset`                 | Wipe data — **only when `MODE=TEST`**    |

---

## Quick start (Docker Compose — recommended)

The simplest way to run the whole stack (database + API + web):

```bash
docker compose up --build
```

Then open **http://localhost:3000** (the API is on **http://localhost:5000**).
Database migrations are applied automatically on backend startup.

Override ports/credentials with environment variables (or a `.env` file next to
`docker-compose.yml`):

```bash
BACKEND_PORT=5055 FRONTEND_PORT=8088 DB_PORT=5456 \
REACT_APP_API_BASE_URL=http://localhost:5055 \
docker compose up --build
```

> `REACT_APP_API_BASE_URL` is baked into the front-end bundle **at build time**,
> so it must point at the URL the browser will use to reach the API. If you change
> `BACKEND_PORT`, set `REACT_APP_API_BASE_URL` to match and rebuild.

Stop and remove everything (including the DB volume):

```bash
docker compose down -v
```

---

## Manual setup (without Docker)

### Prerequisites

- Node.js 18+ (tested on Node 22)
- A running PostgreSQL instance

### 1. Database

Create a database, or spin one up quickly with Docker:

```bash
docker run -d --name smas-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=singmeasong -p 5432:5432 postgres:14
```

### 2. Back-end

```bash
cd back-end
cp .env.example .env          # then edit DATABASE_URL / PORT / MODE
npm install
npx prisma migrate deploy     # apply migrations
npm run dev                   # dev server with hot reload (tsx)
# or for production:
npm run build && npm start
```

### 3. Front-end

```bash
cd front-end
cp .env.example .env          # set REACT_APP_API_BASE_URL (e.g. http://localhost:5000)
npm install
npm start                     # dev server on http://localhost:3000
# or build a static bundle:
npm run build
```

---

## Environment variables

### back-end (`back-end/.env`) — see `back-end/.env.example`

| Variable       | Required | Description                                                        |
| -------------- | -------- | ------------------------------------------------------------------ |
| `DATABASE_URL` | yes      | PostgreSQL connection string used by Prisma                        |
| `PORT`         | no       | API port (defaults to `5000`)                                      |
| `MODE`         | no       | Set to `TEST` to expose `/tests/reset` (used by E2E). Otherwise `DEV` |

A separate `back-end/.env.test` (same keys, a dedicated test database, `MODE=TEST`)
is used by the Jest test scripts.

### front-end (`front-end/.env`) — see `front-end/.env.example`

| Variable                  | Required | Description                                  |
| ------------------------- | -------- | -------------------------------------------- |
| `REACT_APP_API_BASE_URL`  | yes      | Base URL of the back-end API (build-time)    |

> **Secrets are never committed.** `.env` files are git-ignored (only
> `.env.example` templates are tracked). Use real credentials only in your local
> `.env` files or your host's secret manager.

---

## Testing

```bash
# Back-end (needs PostgreSQL + back-end/.env.test)
cd back-end
npm run test:unit          # unit tests
npm run test:integration   # integration tests (Supertest)

# Front-end E2E (needs both apps running, MODE=TEST on the back-end)
cd front-end
npx cypress open
```

> ⚠️ The Cypress E2E suite currently has setup gaps — see
> [Known limitations](#known-limitations--future-improvements).

---

## Deployment

This repo ships a production-ready Docker setup:

- `back-end/Dockerfile` — multi-stage build (`tsc` + `prisma generate`), slim
  runtime; the entrypoint runs `prisma migrate deploy` before launching.
- `front-end/Dockerfile` — builds the CRA bundle and serves it with nginx
  (SPA fallback routing). API URL is injected via the
  `REACT_APP_API_BASE_URL` build arg.
- `docker-compose.yml` — orchestrates Postgres + API + web with health checks.

### Deploying to a cloud host

Any host that runs containers or a Node app + managed Postgres works:

- **Render / Railway / Fly.io** — deploy the `back-end` Docker image, attach a
  managed PostgreSQL, set `DATABASE_URL` (+ `PORT`, `MODE=DEV`). Deploy the
  `front-end` image (or its static `build/`) with `REACT_APP_API_BASE_URL` set
  to the public API URL.
- **Vercel / Netlify (front-end) + Render/Railway (back-end + DB)** — build the
  front-end with `REACT_APP_API_BASE_URL` pointing at the deployed API.

Because CRA inlines env vars at build time, always set `REACT_APP_API_BASE_URL`
**before** building the front-end image/bundle.

---

## Fixes & improvements made

The imported project did not run as-is. Repairs applied on this branch:

- **Back-end would not start on modern Node** — `ts-node` 10.7 throws
  `ERR_UNKNOWN_FILE_EXTENSION ".ts"` under Node 18+/ESM. Switched the `dev` /
  `dev:test` scripts to **`tsx`**, which runs TypeScript ESM reliably.
- **No production build path** — added a `build` script
  (`prisma generate && tsc`) and fixed `start` to run the real entrypoint
  (`node dist/server.js` instead of the non-existent `dist/index.js`).
- **Build output layout** — set `rootDir`/`include`/`exclude` and `target` in
  `tsconfig.json` so the compiler emits a clean `dist/server.js`.
- **Broken ESM imports** — added missing `.js` extensions in
  `testController.ts` / `testService.ts` (required by Node's ESM resolver).
- **Missing/incomplete env docs** — added `back-end/.env.example` and completed
  `front-end/.env.example` with a usable default.
- **Deployment** — added Dockerfiles, an nginx SPA config, auto-migrating
  entrypoint, and a `docker-compose.yml` for one-command deployment.

### Verified working

All API endpoints (create / list / vote / top / random), CORS, the production
`tsc` build + `node dist/server.js`, the CRA production build, and the full
Docker Compose stack were exercised end-to-end. The deployed front-end renders
and successfully reads/writes through the API to PostgreSQL.

---

## Known limitations & future improvements

- **Cypress E2E suite is incomplete** — custom commands and the
  `/tests/reset` URL are out of sync with the specs (e.g. `cy.resetPosts` is
  referenced but not defined; `cy.resetData` targets `/reset` instead of
  `/tests/reset`), and some specs import a missing `utils/setup.js`. Needs a
  pass to make the suite runnable.
- **No automated test in CI** — adding a GitHub Actions workflow would catch
  regressions (build + unit/integration tests).
- **Dependency versions are dated** — Prisma 3, Jest 28, CRA 5 and several
  packages report `npm audit` advisories; a careful upgrade is recommended.
- **No request logging / health endpoint** — a `/health` route and structured
  logging would help production operations.
- **`prisma.seed` points at a non-existent `prisma/seed.ts`** — either add a
  seed script or remove the config.

See the repository Issues for tracked follow-ups.

---

<sub>Part of the **ai-training-workspace-may** workspace.</sub>
