# Sing Me a Song 🎵

> Workspace: `ai-training-workspace-may` — branch `b78ada67-claude-4-8`
> Source project imported from [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song).

A full-stack app for sharing and voting on YouTube music recommendations. Anyone
can add a song, up/down‑vote it, browse the **Home** feed, see the **Top** list, or
get a score‑weighted **Random** pick. Songs that fall below a score of `-5` are
automatically removed.

This branch repairs the imported project so it builds, tests, runs, and deploys
cleanly on modern toolchains (Node 18/22), and adds a one‑command Docker
deployment.

---

## Project overview

| Layer    | Stack |
|----------|-------|
| Frontend | React 18 (Create React App), React Router 6, styled-components, axios, react-player |
| Backend  | Node.js, Express 4, TypeScript (ESM), Joi validation |
| Database | PostgreSQL via Prisma ORM |
| Tests    | Jest + Supertest (backend unit & integration), Cypress (frontend E2E) |

### Repository layout

```
.
├── back-end/          # Express + TypeScript + Prisma API
├── front-end/         # React (Create React App) client
├── docker-compose.yml # One-command full-stack deployment
└── .env.example       # Root-level compose overrides
```

### API endpoints

| Method | Route                              | Description                          |
|--------|------------------------------------|--------------------------------------|
| POST   | `/recommendations`                 | Create a recommendation (201)        |
| GET    | `/recommendations`                 | List the 10 newest recommendations   |
| GET    | `/recommendations/random`          | Get a score-weighted random pick     |
| GET    | `/recommendations/top/:amount`     | Top `:amount` by score               |
| GET    | `/recommendations/:id`             | Get one recommendation by id         |
| POST   | `/recommendations/:id/upvote`      | +1 score                             |
| POST   | `/recommendations/:id/downvote`    | -1 score (removed when score < -5)   |
| DELETE | `/tests/reset`                     | Reset DB (only when `MODE=TEST`)     |

---

## Required environment variables

### Back-end (`back-end/.env`) — see `back-end/.env.example`

| Variable        | Required | Example | Description |
|-----------------|----------|---------|-------------|
| `DATABASE_URL`  | yes | `postgresql://postgres:postgres@localhost:5432/singmeasong?schema=public` | Postgres connection string used by Prisma |
| `PORT`          | no  | `5000` | API listen port (defaults to 5000) |

For the test database use `back-end/.env.test` (see `back-end/.env.test.example`),
which additionally sets `MODE=TEST` and **must point at a separate database** —
the test suite truncates/resets it.

### Front-end (`front-end/.env`) — see `front-end/.env.example`

| Variable                  | Required | Example | Description |
|---------------------------|----------|---------|-------------|
| `REACT_APP_API_BASE_URL`  | yes | `http://localhost:5000` | Base URL of the API (baked into the bundle at build time) |

> 🔒 **Secrets are never committed.** Real `.env` files are git-ignored; only
> `.env.example` templates are tracked. Use strong credentials in production.

---

## Local setup (without Docker)

**Prerequisites:** Node.js 18+ and a running PostgreSQL instance.

### 1. Database

Either point `DATABASE_URL` at an existing Postgres, or start one quickly:

```bash
docker run -d --name smas-postgres \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=singmeasong \
  -p 5432:5432 postgres:14-alpine
```

### 2. Back-end

```bash
cd back-end
cp .env.example .env            # adjust DATABASE_URL if needed
npm install
npx prisma migrate deploy       # apply migrations
npm run dev                     # http://localhost:5000  (hot-reload)
```

Other useful scripts:

```bash
npm run build   # compile TypeScript to dist/ (prisma generate + tsc)
npm start       # run the compiled server (node dist/server.js)
npm test        # reset test DB + run Jest unit & integration suites
```

> The test suite expects a separate test database. Copy
> `back-end/.env.test.example` to `back-end/.env.test` first.

### 3. Front-end

```bash
cd front-end
cp .env.example .env            # REACT_APP_API_BASE_URL=http://localhost:5000
npm install
npm start                       # http://localhost:3000
```

---

## Deployment (Docker Compose)

The whole stack — Postgres, API and web client — runs with a single command:

```bash
docker compose up --build
```

- Web client → <http://localhost:3000>
- API        → <http://localhost:5000>

The backend container automatically runs `prisma migrate deploy` on startup, so
the schema is created on first boot. Database data persists in the `db-data`
volume. Stop with `docker compose down` (add `-v` to also drop the data volume).

Override defaults (credentials, API URL) by copying `.env.example` to `.env` at
the repo root before running compose.

> **Note on `REACT_APP_API_BASE_URL`:** it is compiled into the static bundle at
> build time and must be reachable **from the user's browser** — use the public
> host address (e.g. `http://localhost:5000` locally), not the internal Docker
> service name.

---

## Fixes & improvements made on this branch

1. **Backend wouldn't start under Node 22 ESM** — `nodemon src/server.ts` ran
   `ts-node` directly, which can't load `.ts` as ES modules. Upgraded `ts-node`
   to `^10.9.2` (fixes the `ERR_LOADER_CHAIN_INCOMPLETE` loader bug) and added a
   `nodemon.json` + `register-ts-node.mjs` that registers the ESM loader.
2. **Crash on startup from extensionless imports** — `testController.ts` and
   `testService.ts` imported modules without the `.js` extension required by
   Node ESM. Added the extensions.
3. **Test suite couldn't reset the DB** — `prisma migrate reset` failed
   non-interactively; added `--force` and the `--` separator so the flag reaches
   Prisma instead of being swallowed by `dotenv-cli`.
4. **Test factory used a missing dependency** — `recommendationFactory.ts` did
   `require("random-youtube-music-video")` (not installed, and `require` is
   undefined in ESM). Replaced with a deterministic faker-based generator.
5. **Faulty integration assertion** — the "List recommendations" test expected
   an impossible ordering; corrected it to the API's actual newest-first order.
6. **Production scripts were broken** — `start` pointed at a non-existent
   `dist/index.js` and there was no `build` script. Added `build`
   (`prisma generate && tsc`), fixed `start` to `node dist/server.js`, and set
   `rootDir`/`include` in `tsconfig.json` so output lands at `dist/server.js`.
7. **Frontend build failed in CI** — unused `Component` import in `App.js` was
   treated as an error. Removed it.
8. **Missing/incomplete env templates** — added `back-end/.env.example`,
   `back-end/.env.test.example` and completed `front-end/.env.example`.
9. **Added containerized deployment** — Dockerfiles for both apps, an nginx SPA
   config, and a root `docker-compose.yml` for one-command deploys.

After the fixes: **26/26 backend tests pass**, both apps build cleanly, and the
React UI renders live data fetched from the API end-to-end.

---

## Known limitations & future improvements

- **Cypress E2E suite is outdated.** The specs reference a wrong reset URL
  (`/reset` instead of `/tests/reset`), an undefined `cy.resetPosts()` command,
  and a missing `cypress/e2e/utils/setup.js`. The default CRA "advanced examples"
  specs are also still present. These need a cleanup pass (tracked as a GitHub
  issue).
- **No server-side CORS allow-list.** CORS is currently open (`*`). For
  production, restrict it to the known frontend origin.
- **Dependency vulnerabilities.** `npm audit` reports advisories in the
  (older) toolchain. A dependency-upgrade pass is recommended.
- **No CI pipeline.** Adding GitHub Actions to run build + tests on PRs would
  guard against regressions.

---

## Original Create React App documentation

The original front-end documentation is preserved unchanged in
[`front-end/README.md`](front-end/README.md).
