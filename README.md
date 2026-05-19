# Sing me a Song

Full-stack music recommendation app: users post YouTube links, vote on
them, and browse the top picks or a random one. Forked from
[ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song)
and repaired so it builds, boots and tests on current toolchains.

- **Back-end** — Node.js + Express + Prisma over PostgreSQL.
- **Front-end** — React 18 (Create React App) + styled-components.
- **Tests** — Jest (unit + integration) on the back-end, Cypress on the
  front-end.

## Project layout

```
.
├── back-end/        Express API, Prisma schema and migrations, Jest suites
├── front-end/       React app, Cypress e2e suite
└── docker-compose.yml   One-command local/deploy stack (db + api + web)
```

## Prerequisites

- Node.js 20 (the upstream project predates Node 22's loader changes,
  see *Fixes* below for the toolchain swap).
- npm 9+.
- PostgreSQL 14+ reachable on the `DATABASE_URL` set in `.env`.
- Optional: Docker / Docker Compose for the bundled deploy.

## Local setup

```bash
# 1. Database (any PostgreSQL works; this is the quickest path)
sudo service postgresql start
sudo -u postgres psql -c "CREATE USER singme WITH PASSWORD 'singme' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE singmeasong OWNER singme;"
sudo -u postgres psql -c "CREATE DATABASE singmeasong_test OWNER singme;"

# 2. Back-end
cd back-end
cp .env.example .env            # then edit DATABASE_URL / PORT
cp .env.test.example .env.test  # only needed if you intend to run the test suite
npm install
npx prisma migrate deploy
npx prisma generate
npm run dev                     # http://localhost:5000

# 3. Front-end (new terminal)
cd front-end
cp .env.example .env            # point REACT_APP_API_BASE_URL at the API
CYPRESS_INSTALL_BINARY=0 npm install --legacy-peer-deps
npm start                       # http://localhost:3000
```

`CYPRESS_INSTALL_BINARY=0` skips Cypress' optional binary download. Drop
it if you need to run `npx cypress open` locally and have network
access to download.cypress.io.

## Environment variables

### `back-end/.env`

| Variable       | Required | Example                                                                | Purpose                                              |
| -------------- | -------- | ---------------------------------------------------------------------- | ---------------------------------------------------- |
| `DATABASE_URL` | yes      | `postgresql://singme:singme@localhost:5432/singmeasong?schema=public`  | Prisma connection string used at runtime + migrations |
| `PORT`         | no       | `5000`                                                                 | HTTP port the Express app listens on                  |
| `MODE`         | no       | `TEST`                                                                 | Set to `TEST` to expose the `/tests/reset` route used by the e2e suite |

### `back-end/.env.test`

Same shape as `.env` but pointed at a disposable database. The Jest
suite truncates this database between cases, so do not point it at any
data you care about. The `dev:test` and `test` scripts read it via
`dotenv-cli`.

### `front-end/.env`

| Variable                 | Required | Example                  | Purpose                              |
| ------------------------ | -------- | ------------------------ | ------------------------------------ |
| `REACT_APP_API_BASE_URL` | yes      | `http://localhost:5000`  | Axios `baseURL` for the React client |

Never commit a real `.env`. Both `.gitignore` files already exclude
them; only the `.env.example` files are tracked.

## Available scripts

### Back-end

| Command                  | What it does                                                          |
| ------------------------ | --------------------------------------------------------------------- |
| `npm run dev`            | Boots the API with `tsx watch` (hot reload).                           |
| `npm run build`          | Type-checks and emits compiled JS to `dist/`.                          |
| `npm start`              | Runs the compiled `dist/server.js` (use after `npm run build`).         |
| `npm run migrate:deploy` | Applies pending Prisma migrations (use in deploy pipelines).            |
| `npm run migrate:dev`    | Interactive migration generator (use during development).               |
| `npm run test:unit`      | Jest unit tests against the test database.                              |
| `npm run test:integration` | Jest integration tests against the test database.                     |
| `npm test`               | Resets the test database, then runs the full Jest suite.                |

### Front-end

| Command          | What it does                                  |
| ---------------- | --------------------------------------------- |
| `npm start`      | CRA dev server with HMR on `:3000`.            |
| `npm run build`  | Production bundle in `front-end/build/`.       |
| `npm test`       | React Testing Library suite.                   |
| `npx cypress open` | Cypress e2e runner (requires the binary).    |

## API surface

```
GET    /health                          → { status: "ok" }
GET    /recommendations                 → 10 most recent recommendations
POST   /recommendations { name, youtubeLink } → 201
GET    /recommendations/random          → one recommendation, weighted by score
GET    /recommendations/top/:amount     → top N by score
GET    /recommendations/:id             → recommendation by id (404 if absent)
POST   /recommendations/:id/upvote      → +1 score
POST   /recommendations/:id/downvote    → -1 score (delete when score < -5)
DELETE /tests/reset                     → only when MODE=TEST (Cypress hook)
```

`youtubeLink` is validated against `^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$`.

## Deployment

### Docker Compose (recommended, one command)

```bash
docker compose up --build -d
docker compose logs -f backend
```

This spins up:

- `db` — Postgres 16 with a named volume.
- `backend` — runs `prisma migrate deploy` then `node dist/server.js`
  on `:5000` (Dockerfile builds with `tsc`).
- `frontend` — multi-stage build: CRA → nginx serving the static
  bundle on `:3000`. The API URL is baked at build time via the
  `REACT_APP_API_BASE_URL` build arg.

Override the API URL for a real deployment by exporting it before the
build:

```bash
REACT_APP_API_BASE_URL=https://api.example.com docker compose up --build -d
```

Customise the database credentials via `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB` env vars before running `up`.

### Manual deploys (Railway, Render, Fly, etc.)

- Back-end: deploy `back-end/` with the `Dockerfile`. Provide
  `DATABASE_URL` (and optionally `PORT`); the container runs
  `prisma migrate deploy` on start.
- Front-end: deploy `front-end/` as a static site. Build with
  `REACT_APP_API_BASE_URL=<your-api-url> npm run build` and serve
  `front-end/build/`. Vercel/Netlify both work; on Render use a
  Static Site service.

A `/health` endpoint is exposed on the API for load balancer probes.

## Fixes applied on this branch

Everything inherited from the upstream repo that prevented the app
from building or running on Node 20+/22 was repaired here. Highlights:

- **Back-end ESM bootstrap** — `ts-node 10.7` does not support Node 22's
  loader API; the server crashes on the very first `import "./app.js"`.
  Swapped the dev runner for `tsx` and added a real `tsc` build so
  `npm start` runs the compiled output.
- **Test factory** — `random-youtube-music-video` returns a `Promise`
  but was used as a synchronous string, so every integration test
  posted invalid links and got `422`s. Rebuilt the factory around a
  deterministic faker-generated link that matches the Joi regex.
- **Missing `.js` extensions** on test service/controller imports under
  ESM (`testService` / `testController`).
- **Prisma client import** — replaced the
  `import pkg from "@prisma/client"` destructure with a dual-mode shim
  so the same source works under both native ESM (server) and ts-jest's
  CJS interop (tests).
- **List ordering assertion** — the integration test expected an order
  no API ever returns. Corrected to the actual `id DESC` order.
- **CRA build** — removed the unused `Component` import that CRA's
  CI lint blocks the build on.
- **Env templates** — both `.env.example` files were missing values
  (`REACT_APP_API_BASE_URL=http://`) or absent (`back-end/.env.example`).
- **Health probe** — added `GET /health` for deployment liveness checks.
- **App identity** — replaced "React App" page title and CRA boilerplate
  meta description.

## Known limitations / future improvements

- The recommendation list endpoint is hard-coded to `take: 10`. A real
  product needs pagination (or at least a query-string `limit`).
- CORS is fully open (`app.use(cors())`). Lock it down to the deployed
  front-end origin before going to production.
- Front-end has no error UI beyond `alert()` for vote/create failures.
- `npm audit` reports a long list of CVEs in the upstream `react-scripts 5`
  + `cypress 10` dev chain. They are dev-only but worth tracking.
- No CI workflow yet (`.github/workflows/` is empty).
- The integration test ordering is sensitive to insertion order; a
  follow-up could rewrite the assertions in a set-based way.
