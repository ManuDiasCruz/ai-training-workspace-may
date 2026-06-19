# Sing Me a Song 🎵

A full-stack web app for sharing and voting on song recommendations. Anyone can
post a song (a name + a YouTube link), up/down-vote recommendations, browse the
latest, the top-rated, or a (score-weighted) random pick. Songs that fall below
a score of **-5** are automatically removed.

This branch (`claude-29f0b72b-sing-me-a-song`) imports the original project from
[ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song)
and repairs it so it runs, tests, builds and deploys cleanly on modern tooling.
See [What was fixed](#-what-was-fixed) below.

---

## 🏗️ Architecture

| Layer | Stack |
| --- | --- |
| **Back-end** (`back-end/`) | Node.js + Express + TypeScript (ESM), Prisma ORM, PostgreSQL, Joi validation. Runs with `tsx` in dev and compiled JS in production. |
| **Front-end** (`front-end/`) | React 18 (Create React App), React Router v6, axios, styled-components, `react-player`. |
| **Tests** | Back-end: Jest + Supertest (unit + integration). Front-end: Cypress (e2e). |
| **Deployment** | Docker Compose: PostgreSQL + back-end (Node) + front-end (nginx, with same-origin API proxy). |

### Data model

A single `Recommendation` table: `id`, `name` (unique), `youtubeLink`, `score` (default `0`).

### REST API

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/recommendations` | Create a recommendation (`{ name, youtubeLink }`) |
| `GET` | `/recommendations` | List the 10 most recent (id desc) |
| `GET` | `/recommendations/:id` | Get one by id |
| `GET` | `/recommendations/random` | Get a score-weighted random recommendation |
| `GET` | `/recommendations/top/:amount` | Top `:amount` by score |
| `POST` | `/recommendations/:id/upvote` | +1 score |
| `POST` | `/recommendations/:id/downvote` | -1 score (deletes if score < -5) |
| `DELETE` | `/tests/reset` | Test-only: truncate the table (**requires `MODE=TEST`**) |

---

## ✅ Prerequisites

- **Node.js 18+** (verified on Node 22) and **npm**
- **Docker** + **Docker Compose** (for PostgreSQL and/or the full stack)

---

## 🔐 Environment variables

Secrets are **never** committed. Each app ships an `.env.example`; copy it to
`.env` and fill in real values (the `.env*` files are git-ignored).

### Back-end (`back-end/.env`)

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | PostgreSQL connection string used by Prisma (`postgresql://user:pass@host:port/db?schema=public`) |
| `PORT` | no | HTTP port (default `5000`) |
| `MODE` | no | Set to `TEST` to expose `DELETE /tests/reset` (used by the e2e suite). Leave unset in production. |

A separate `back-end/.env.test` (also git-ignored) provides `DATABASE_URL` for
the **test** database and `MODE=TEST`.

### Front-end (`front-end/.env`)

| Variable | Required | Description |
| --- | --- | --- |
| `REACT_APP_API_BASE_URL` | yes (dev) | Base URL of the back-end API, e.g. `http://localhost:5000`. Leave empty to use same-origin requests (the Docker deployment proxies the API through nginx). |

---

## 🚀 Quick start with Docker Compose (recommended)

Brings up PostgreSQL, the back-end and the nginx-served front-end together. The
front-end calls the API on its own origin and nginx proxies it to the back-end
(no CORS, no hard-coded host/port baked into the bundle).

```bash
docker compose up -d --build
```

- Front-end: <http://localhost:8090>
- Back-end (direct, for debugging): <http://localhost:5060/recommendations>

Override ports/credentials via env vars (see `docker-compose.yml`):
`FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_USER/PASSWORD/DB`, `MODE`,
`REACT_APP_API_BASE_URL`.

Stop / clean up:

```bash
docker compose down          # stop
docker compose down -v       # stop and delete the database volume
```

---

## 🧑‍💻 Local development (without Docker for the apps)

### 1. Start a PostgreSQL instance

```bash
docker run -d --name smas-db -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres -e POSTGRES_DB=sing_me_a_song \
  -p 5432:5432 postgres:14
```

### 2. Back-end

```bash
cd back-end
cp .env.example .env                # then edit DATABASE_URL/PORT
npm install
npx prisma migrate deploy           # create the schema
npm run dev                         # http://localhost:5000  (tsx watch)
```

Production build:

```bash
npm run build      # tsc -> dist/
npm start          # node dist/server.js
```

### 3. Front-end

```bash
cd front-end
cp .env.example .env                # REACT_APP_API_BASE_URL=http://localhost:5000
npm install
npm start                           # http://localhost:3000
```

---

## 🧪 Tests

### Back-end (Jest)

Requires `back-end/.env.test` pointing at a **test** database (it is reset on
every run).

```bash
cd back-end
npm test               # resets test DB, runs unit + integration (26 tests)
npm run test:unit
npm run test:integration
```

### Front-end (Cypress e2e)

The e2e suite needs the front-end, the back-end (with `MODE=TEST`) and the
database all running. Targets are configurable via `CYPRESS_BASE_URL` and
`CYPRESS_API_URL`.

```bash
# Against the Docker stack started with MODE=TEST:
MODE=TEST docker compose up -d --build
cd front-end
CYPRESS_BASE_URL=http://localhost:8090 CYPRESS_API_URL=http://localhost:8090 \
  npx cypress run --spec "cypress/e2e/spec.recommendation.cy.js"
```

---

## 🛠️ What was fixed

The original project did not run out of the box on a fresh, modern environment.
The following bugs were repaired with minimal, targeted changes:

**Back-end**
- **Env not loaded** – `DATABASE_URL` was never read at runtime (Prisma does not
  auto-load `.env`), so the server crashed on the first query. Now `dotenv` is
  loaded at startup.
- **Broken ESM imports** – `testController`/`testService` imported without the
  required `.js` extension, throwing `ERR_MODULE_NOT_FOUND` and crashing boot.
- **Dev runner broken on Node 18+/22** – `ts-node`'s ESM loader fails with
  `ERR_LOADER_CHAIN_INCOMPLETE`. Switched the dev/build/start scripts to `tsx`
  and added a real `build` (`tsc`) and a correct `start` (`node dist/server.js`,
  was the non-existent `dist/index.js`).
- **Unrunnable test scripts** – `dotenv-cli` was swallowing command flags
  (`--force`, `-i`, …) for lack of a `--` separator, so `prisma migrate reset`
  failed in CI and `npm test` never reached Jest. Added the separator + `--force`.
- **Broken test factory** – the data factory `require`d an uninstalled package
  (`random-youtube-music-video`) and used `require` in an ESM module. Replaced
  with a `faker`-generated, schema-valid YouTube URL.
- **Wrong test assertion** – the "list recommendations" integration test
  asserted an impossible order; corrected to match `id desc`.

**Front-end / e2e**
- **Wrong reset route** – Cypress `resetData()` hit `/reset`; the real route is
  `/tests/reset`. Made the API/base targets configurable and use same-origin.
- **Undefined variables** – the "Add a song" spec used undefined `name`/`youtubeLink`.
- **Impossible assertion** – the ">= 10 posts" spec used invalid links and a
  selector that did not exist; now uses valid songs and a `data-identifier`
  hook on the vote row.

**Tooling / docs**
- Added `back-end/.env.example`, completed `front-end/.env.example`, root
  `.gitignore`, Docker/Compose files and this README.

After these fixes (all verified on this branch):

- ✅ Back-end REST API works end-to-end against PostgreSQL
- ✅ **26/26** Jest tests pass (unit + integration)
- ✅ Front-end builds (`react-scripts build`)
- ✅ Dockerized stack builds and serves the integrated app
- ✅ **5/5** Cypress e2e specs pass against the deployed stack
  (real browser → nginx → API → DB)

---

## ⚠️ Known limitations & future improvements

- **Dependency vulnerabilities / outdated stack** – Prisma 3, CRA 5 and several
  deps are old and report `npm audit` issues. Upgrading (Prisma 5+, Vite, etc.)
  is recommended but out of scope for a minimal repair.
- **`POST /recommendations` returns no body** – it responds `201` with no
  payload, so clients can't learn the new `id` without re-fetching. Returning
  the created resource would be more RESTful.
- **Non-numeric `:id` causes a 500** – e.g. `/recommendations/abc/upvote`
  reaches Prisma as `NaN` and 500s instead of returning `400/404`. Add id
  validation.
- **No CI pipeline** – tests are not run automatically on push/PR.
- **No managed cloud deployment** – the included Docker Compose is intended for a
  single host/VPS; a managed setup (e.g. Render/Railway for API + DB, Vercel/
  Netlify for the SPA) would be a good next step.

---

## 📄 Front-end Create React App notes

The original CRA-generated documentation is preserved at
[`front-end/README.md`](front-end/README.md).
