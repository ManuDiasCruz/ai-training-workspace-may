# 🎵 Sing me a Song

A full-stack song-recommendation app. Users submit YouTube song recommendations,
up/down-vote them, and browse them in three ways: the **home** timeline (most
recent), the **top** ranking (highest score), and a weighted **random** pick.
Recommendations that fall below a score of **-5** are automatically removed.

> This branch (`48-he-sing-me-a-song`) imports the project from
> [`ManuDiasCruz/sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song)
> and repairs it so it builds, runs, tests, and deploys cleanly. See
> [**Fixes & improvements**](#-fixes--improvements-made) for the full list.

---

## 🧱 Tech stack

| Layer      | Technology                                                        |
| ---------- | ----------------------------------------------------------------- |
| Front-end  | React 18 (Create React App), React Router 6, axios, styled-components, react-player |
| Back-end   | Node.js + TypeScript (ESM), Express, Prisma ORM, Joi validation   |
| Database   | PostgreSQL                                                        |
| Tests      | Jest + Supertest (back-end unit & integration), Cypress (front-end E2E) |

## 📁 Repository structure

```
.
├── back-end/            # Express + Prisma API (TypeScript, ESM)
│   ├── prisma/          # schema, migrations, seed
│   ├── src/             # app, routers, controllers, services, repositories
│   ├── tests/           # Jest unit + integration tests
│   ├── Dockerfile
│   └── .env.example / .env.test.example
├── front-end/           # React (CRA) client
│   ├── src/
│   ├── cypress/         # E2E tests
│   ├── Dockerfile + nginx.conf
│   ├── README.md        # original Create React App documentation (preserved)
│   └── .env.example
├── docker-compose.yml   # full local stack: db + api + web
└── render.yaml          # Render.com blueprint (managed Postgres + api + web)
```

---

## ✅ Prerequisites

- **Node.js 20+** and npm
- **PostgreSQL 14+** running locally (or use Docker Compose, which provides it)

---

## 🔐 Environment variables

Nothing sensitive is committed. Copy the example files and fill in your own values.
The real `.env*` files are git-ignored.

### Back-end — `back-end/.env` (copy from `.env.example`)

| Variable       | Required | Description                                                        |
| -------------- | -------- | ------------------------------------------------------------------ |
| `DATABASE_URL` | yes      | PostgreSQL connection string used by Prisma.                       |
| `PORT`         | no       | API port (default `5000`).                                         |

### Back-end tests — `back-end/.env.test` (copy from `.env.test.example`)

| Variable       | Required | Description                                                        |
| -------------- | -------- | ------------------------------------------------------------------ |
| `DATABASE_URL` | yes      | Connection string for a **separate** test database (it is reset).  |
| `PORT`         | no       | Port used in test mode (default `5001`).                           |
| `MODE`         | yes      | Must be `TEST` to expose the `/tests/reset` helper route.          |

### Front-end — `front-end/.env` (copy from `.env.example`)

| Variable                  | Required | Description                                              |
| ------------------------- | -------- | -------------------------------------------------------- |
| `REACT_APP_API_BASE_URL`  | yes      | Base URL of the API, e.g. `http://localhost:5000`.       |

---

## 🚀 Local setup

### 1. Back-end

```bash
cd back-end
npm install

# Configure environment
cp .env.example .env          # then edit DATABASE_URL to point at your Postgres

# Create the schema
npx prisma migrate deploy     # or: npx prisma migrate dev
npm run seed                  # optional: insert a few sample recommendations

# Run in development (auto-reload)
npm run dev                   # API on http://localhost:5000
```

### 2. Front-end

```bash
cd front-end
npm install

cp .env.example .env          # REACT_APP_API_BASE_URL=http://localhost:5000
npm start                     # app on http://localhost:3000
```

Open http://localhost:3000 — the timeline should load recommendations from the API.

---

## 🧪 Tests

### Back-end (Jest)

```bash
cd back-end
cp .env.test.example .env.test   # point DATABASE_URL at a dedicated test DB

npm run test:unit        # 14 unit tests
npm run test:integration # 12 integration tests (uses the test DB)
npm test                 # resets the test DB, then runs everything (26 tests)
```

### Front-end (Cypress)

```bash
cd front-end
# With the API running in TEST mode (MODE=TEST) and the app served,
npx cypress open      # interactive
npx cypress run       # headless
```

---

## 🏗️ Production build

```bash
# Back-end
cd back-end
npm run build     # prisma generate + tsc -> dist/
npm start         # node dist/server.js

# Front-end
cd front-end
npm run build     # -> build/ (static assets)
npx serve -s build
```

---

## ☁️ Deployment

The app is a standard Node API + PostgreSQL + static React bundle. Any of the
following works; pick one.

### Option A — Docker Compose (self-hosted, one command)

```bash
docker compose up --build
# Front-end: http://localhost:3000   API: http://localhost:5000
```

This starts PostgreSQL, builds and runs the API (applying migrations on boot),
and serves the built front-end via nginx.

### Option B — Render.com (managed, free tier) via `render.yaml`

1. Push this branch to GitHub.
2. In Render: **New → Blueprint** and select the repo/branch. Render reads
   [`render.yaml`](render.yaml) and provisions a free PostgreSQL database, the
   API web service, and the static front-end.
3. Confirm the front-end's `REACT_APP_API_BASE_URL` matches the API URL Render
   assigns, then redeploy the front-end if needed.

### Option C — Split hosting

- **API + DB**: Render / Railway / Fly.io (set `DATABASE_URL`; run
  `npx prisma migrate deploy` on release; start with `npm start`).
- **Front-end**: Netlify / Vercel / GitHub Pages / any static host. Set
  `REACT_APP_API_BASE_URL` to the deployed API URL and enable SPA fallback
  (rewrite all routes to `/index.html`).

> **Note on this repository:** it is currently **private** with GitHub Pages
> disabled, and a live public deployment requires a hosting account. The
> production builds and the deployment configs above have been verified to build
> and run locally in production mode; provisioning a public URL is the only
> remaining step and needs the owner's hosting credentials.

---

## 🛠️ Fixes & improvements made

The imported project did not build, run, or test on a current (Node 20) setup.
The following **minimal, targeted** fixes were applied:

**Back-end**
- **ESM module resolution** — added the missing `.js` extensions to relative
  imports in `testController.ts` and `testService.ts`. Node's ESM loader
  requires them, and because `app.ts` imports the test router unconditionally,
  the whole server failed to start.
- **ts-node on Node 20** — bumped `ts-node` `10.7.0 → 10.9.2` to fix
  `ERR_LOADER_CHAIN_INCOMPLETE`, and changed `dev`/`dev:test` to run via
  `nodemon --exec "node --loader ts-node/esm"` (the bare `nodemon src/server.ts`
  could not find ts-node and did not enable ESM).
- **Runtime env loading** — `server.ts` now imports `dotenv/config`, so
  `DATABASE_URL`/`PORT` are loaded when running the server.
- **Production build/start** — added a real `build` script (`prisma generate &&
  tsc`) and fixed `start` to `node dist/server.js` (it previously pointed at a
  non-existent `dist/index.js` with no build step). Tightened `tsconfig.json`
  (target, `rootDir`, `include`/`exclude`, `skipLibCheck`) so `tsc` emits a
  runnable `dist/`.
- **Tests** — replaced the broken song factory (it used a CommonJS `require`
  for an undeclared `random-youtube-music-video` package) with offline faker
  generation; corrected a wrong ordering assertion; made the scripts
  cross-platform (`cross-env`), added the `dotenv-cli` `--` separator so flags
  reach Prisma/Jest, and added `--force` to `migrate reset` for non-interactive
  runs. **All 26 tests pass.**
- **Tooling** — added `prisma/seed.ts` (sample data), `.env.example`,
  `.env.test.example`, and a `Dockerfile`.

**Front-end**
- Fixed `.env.example` (`REACT_APP_API_BASE_URL` was `http://`, an invalid URL
  that made every request fail) and removed an unused import.
- Added a `Dockerfile` + `nginx.conf` (SPA-aware static serving).

**Repo**
- Added `docker-compose.yml` and `render.yaml` for turnkey deployment.

### Verified working
- Back-end dev server, production build (`dist/`) and `npm start`.
- All REST endpoints: create (201) / invalid (422) / duplicate (409) / upvote /
  downvote / not-found (404) / list / top / random / by-id.
- Front-end (dev **and** production build) integrating with the API: Home, Top,
  Random routes and the create/vote flows.
- Full Jest suite: **26/26** passing.

---

## ⚠️ Known limitations & future improvements

- **Dependency audit** — the pinned React-Scripts 5 / Prisma 3 stack reports
  npm audit warnings. Upgrading (Prisma 5+, etc.) is worthwhile but out of scope
  for these minimal repairs.
- **No live public URL yet** — see the deployment note above; the repo is
  private and needs the owner's hosting credentials to publish.
- **Deprecation warning** — `node --loader ts-node/esm` prints an experimental
  warning on Node 20; migrating to `--import` or `tsx` would remove it.
- **Cypress E2E** — the front-end E2E tests depend on the API running in
  `MODE=TEST`; they are not wired into CI.
- **No CI pipeline** — a GitHub Actions workflow running lint/build/test would
  guard against regressions.

See the repository **Issues** for tracked follow-ups.

---

## 📄 Original documentation

The original Create React App front-end documentation is preserved at
[`front-end/README.md`](front-end/README.md).
