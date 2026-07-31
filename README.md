# 🎵 Sing me a Song

A full-stack song-recommendation app: anyone can post a YouTube link, vote it
up or down, and browse recommendations three ways. A recommendation whose
score drops below **-5** is deleted automatically.

> This branch (`723-fh-singmeasong`) imports the project from
> [`ManuDiasCruz/sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song)
> and repairs it so it installs, runs, passes its tests, builds and deploys.
> The full list of repairs is in [Fixes and improvements](#fixes-and-improvements).
>
> The repository root also carries an unrelated static project (a parrot
> memory card game: `index.html`, `css/`, `img/`, `src/`), which is left
> intact; its original README is preserved unchanged in
> [`docs/parrot-memory-card-game.md`](docs/parrot-memory-card-game.md).

## Overview

| Layer     | Stack                                                                  |
| --------- | ---------------------------------------------------------------------- |
| Front-end | React 18, React Router 6, styled-components, axios (Create React App)  |
| Back-end  | Node 20, Express 4, TypeScript (native ESM), joi                        |
| Database  | PostgreSQL via Prisma 3                                                 |
| Tests     | Jest + supertest (unit and integration), Cypress 10 scaffold (E2E)      |

### Screens

- **home** (`/`) — the 10 most recent recommendations plus the create form
- **top** (`/top`) — the 10 highest-scored recommendations
- **random** (`/random`) — one recommendation, weighted so that ~70% of the
  time it comes from songs scoring above 10

### API

| Method   | Route                           | Behaviour                                                 |
| -------- | ------------------------------- | --------------------------------------------------------- |
| `GET`    | `/health`                       | `{ "status": "ok" }` — liveness probe                     |
| `POST`   | `/recommendations`              | `201`; `409` on duplicate name, `422` on invalid payload  |
| `GET`    | `/recommendations`              | 10 most recent, newest first                              |
| `GET`    | `/recommendations/random`       | one weighted-random song; `404` when the table is empty   |
| `GET`    | `/recommendations/top/:amount`  | highest scored first; `422` on a non-positive `:amount`   |
| `GET`    | `/recommendations/:id`          | one song; `404` when unknown or non-numeric               |
| `POST`   | `/recommendations/:id/upvote`   | score `+1`; `404` when unknown                            |
| `POST`   | `/recommendations/:id/downvote` | score `-1`, deletes the row below `-5`; `404` when unknown |
| `DELETE` | `/tests/reset`                  | truncates the table — **only mounted when `MODE=TEST`**   |

## Setup

Requires **Node 18+** and a **PostgreSQL** instance.

### 1. Database

With Docker:

```bash
docker compose up -d
```

This starts PostgreSQL 16 on `localhost:5432` (user/password `postgres`) and
creates the `singmeasong` and `singmeasong_test` databases on first boot.
Already running your own PostgreSQL? Create those two databases yourself.

### 2. Back-end

```bash
cd back-end
npm install
cp .env.example .env        # adjust DATABASE_URL if needed
npm run migrate:deploy      # applies prisma/migrations
npm run seed                # optional - a few songs to look at
npm run dev                 # http://localhost:5000
```

For the test database, create `.env.test` pointing `DATABASE_URL` at
`singmeasong_test` and set `MODE=TEST`.

### 3. Front-end

```bash
cd front-end
npm install
cp .env.example .env        # REACT_APP_API_BASE_URL=http://localhost:5000
npm start                   # http://localhost:3000
```

## Environment variables

**Never commit real `.env` files** — both packages gitignore `.env*` while
keeping `.env.example` tracked, and no credential is committed on this branch.

### `back-end/.env` (see [`back-end/.env.example`](back-end/.env.example))

| Variable       | Required | Default | Purpose                                                    |
| -------------- | -------- | ------- | ----------------------------------------------------------- |
| `DATABASE_URL` | yes      | —       | PostgreSQL connection string used by Prisma                 |
| `PORT`         | no       | `5000`  | Port the API listens on                                     |
| `MODE`         | no       | unset   | `TEST` mounts `DELETE /tests/reset`; leave unset in prod    |
| `CORS_ORIGIN`  | no       | unset   | Comma-separated origin allowlist; unset allows every origin |

### `front-end/.env` (see [`front-end/.env.example`](front-end/.env.example))

| Variable                 | Required | Default                 | Purpose                                 |
| ------------------------ | -------- | ----------------------- | ---------------------------------------- |
| `REACT_APP_API_BASE_URL` | yes      | `http://localhost:5000` | Base URL of the API, no trailing slash  |

Create React App inlines this value at **build** time — changing it requires a
rebuild.

## Tests

```bash
cd back-end
npm test               # resets the test DB, then runs unit + integration
npm run test:unit
npm run test:integration
```

All **26 tests pass** (14 unit, 12 integration). CI
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs both suites
against a real PostgreSQL service container and builds the front-end with
`CI=true` on every push to this branch.

The Cypress E2E scaffold under `front-end/cypress/` is the untouched CRA/Cypress
example set; writing real E2E specs is listed as future work.

## Deployment

### Verified demo deployment

The repaired production artifacts were deployed and verified end to end:
the compiled API (`dist/server.js`) and the minified front-end bundle
(`build/`, served behind a SPA fallback) were exposed publicly through
[localhost.run](https://localhost.run) tunnels, and the deployed front-end was
exercised in a real browser against the deployed API — listing, creating,
voting and deep-link refreshes all worked with no console errors.

Tunnel URLs are **ephemeral** (they live only as long as the tunnel process),
so they are not listed here. Reproduce with:

```bash
# terminal 1 - API
cd back-end && npm ci && npm run build && npx prisma migrate deploy && npm start

# terminal 2 - expose the API
ssh -R 80:localhost:5000 nokey@localhost.run   # note the printed https URL

# terminal 3 - front-end built against the public API URL
cd front-end && npm ci && REACT_APP_API_BASE_URL=<api-url> npm run build
npx serve -s build -l 4173

# terminal 4 - expose the front-end
ssh -R 80:localhost:4173 nokey@localhost.run
```

### Permanent hosting (Render blueprint included)

[`render.yaml`](render.yaml) provisions the API, the static front-end and a
managed PostgreSQL instance in one step:

1. Render dashboard → **New** → **Blueprint** → pick this repository/branch.
2. Render creates `singmeasong-db`, `singmeasong-api` and `singmeasong-web`,
   injecting `DATABASE_URL` into the API automatically. The API start command
   runs `prisma migrate deploy` before booting, and `/health` is the health
   check.
3. Set `REACT_APP_API_BASE_URL` on `singmeasong-web` to the API URL and
   redeploy (the value is baked in at build time).
4. Optionally set `CORS_ORIGIN` on `singmeasong-api` to the site URL.

The pieces are ordinary and portable to any Node + static host:

```bash
# API - Node service with a PostgreSQL add-on
cd back-end && npm ci && npm run build
npx prisma migrate deploy && npm start          # serves dist/server.js

# Front-end - static bundle behind a SPA fallback
cd front-end && npm ci && REACT_APP_API_BASE_URL=https://your-api npm run build
# publish build/ and rewrite unknown paths to /index.html
```

The SPA fallback is required — without it, refreshing `/top` or `/random`
returns 404 because those routes only exist client-side.

## Fixes and improvements

Every item below was an actual failure observed while running the project.

### The API could not start

- `testController.ts` and `testService.ts` imported their dependencies without
  the `.js` extension required by native ESM. Since `app.ts` statically imports
  the tests router, the resulting `ERR_MODULE_NOT_FOUND` crashed **every**
  server start.
- `ts-node` 10.7 cannot register its ESM loader on Node ≥ 18.19; bumped to
  10.9.2 and made `npm run dev` invoke the loader explicitly through nodemon.
- `tsconfig.json` declared no `target`, so TypeScript emitted ES3 output that
  is invalid for an ESM package; set `ES2020` and scoped compilation to `src/`.

### Configuration

- Nothing ever loaded dotenv, so `PORT`, `MODE` and `DATABASE_URL` from `.env`
  were invisible at runtime (`DELETE /tests/reset` could never be mounted).
- `back-end/.env.example` did not exist; `front-end/.env.example` shipped the
  truncated value `REACT_APP_API_BASE_URL=http://`, which made axios resolve
  every request against the CRA dev server and 404.
- `npm start` pointed at `dist/index.js`, a file the compiler never produces,
  and there was no `build` script at all. Now `build` → `tsc`, `start` →
  `node dist/server.js`.
- Test scripts were broken three ways: `prisma migrate reset` had no `--force`
  (blocked forever on an interactive prompt), dotenv-cli calls were missing the
  `--` separator (flags were swallowed), and `NODE_OPTIONS=... cmd` syntax does
  not work on Windows (now uses the already-installed `cross-env`).
- `package.json` declared a Prisma seed pointing at a file that did not exist;
  added `prisma/seed.ts` with a few songs.
- Removed `react-player` — a React video library — from the API dependencies.

### Runtime behaviour

- `GET /recommendations/abc`, `top/abc` and votes on non-numeric ids passed
  `NaN` to Prisma and surfaced as HTTP 500; they now answer 404/422.
- `/random` in the front-end hung on "Loading..." forever whenever the API
  answered 404 (which it does on an empty database); it now shows the same
  empty-state message as the other pages.
- `App.js` imported an unused `Component`; react-scripts promotes the warning
  to an error whenever `CI=true`, which broke the build on every common host.
- Added `GET /health` and an optional `CORS_ORIGIN` allowlist (unset keeps the
  original allow-all behaviour).

### Tests

Neither jest suite could even load before these fixes:

- The song factory called `require()` on an undeclared package inside an ESM
  module; it now generates valid YouTube links with faker, and suffixes names
  with a uuid so the unique constraint cannot cause flaky collisions.
- Five `expect(...).rejects` assertions were missing `await` and passed no
  matter what the service did.
- The empty-random unit test mocked only the first of the two `findAll` calls
  `getRandom` makes.
- One integration test asserted a list order the repository never produces;
  another read the new row's id from a bodiless `201` response and upvoted
  `/recommendations/undefined/upvote`.
- `scenariosFactory.ts` exported none of its helpers.

### Developer setup

- `docker-compose.yml` + `scripts/init-db.sql` start PostgreSQL and create both
  databases on first boot.
- `render.yaml` describes a complete production deployment.
- A CI workflow runs the full test suite against a real PostgreSQL service
  container and builds the front-end with `CI=true` — the exact setting that
  caught the build failure above.
- The root README documented only the unrelated static game that shares this
  repository; it now documents this project, with the game's README preserved
  at `docs/parrot-memory-card-game.md` and the game files left untouched.

## Known limitations and future improvements

- **No permanent public deployment.** The demo deployment used ephemeral
  tunnels; a permanent one needs a hosting account (the Render blueprint is
  ready to go).
- **Dependencies are old** — Prisma 3, Jest 28, TypeScript 4.6, axios 0.27,
  CRA 5. Nothing is broken, but security patches are major versions away.
- **No real E2E suite** — the Cypress folder still holds the example specs.
- **Votes are unauthenticated and unlimited**; there is no rate limiting.
- **`GET /recommendations` caps at 10 with no pagination**, so older songs are
  unreachable from the home timeline.
- **`getRandom` picks in application code**; `ORDER BY random() LIMIT 1`
  scales better.
- **No structured logging or error tracking** — the error middleware
  `console.log`s and returns a bare 500.

## Credits

Original project by
[@ManuDiasCruz](https://github.com/ManuDiasCruz/sing-me-a-song). This branch
repairs it and adds the setup, testing and deployment tooling described above.
