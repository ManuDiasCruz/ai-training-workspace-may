# 🎵 Sing me a Song

A full-stack song-recommendation app. Anyone can post a YouTube link, vote it up
or down, and browse the results three ways. A recommendation that drops below a
score of **-5** is deleted automatically.

> This branch (`723-oh-singmeasong`) imports the project from
> [`ManuDiasCruz/sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song)
> and repairs it so that it boots, runs, tests, builds and deploys.
> See [Fixes and improvements](#fixes-and-improvements) for the full list.
>
> The repository root also carries an unrelated static project; its original
> documentation is preserved in
> [`docs/parrot-memory-card-game.md`](docs/parrot-memory-card-game.md).

## Overview

| Layer        | Stack                                                                |
| ------------ | -------------------------------------------------------------------- |
| Front-end    | React 18, React Router 6, styled-components, axios (Create React App) |
| Back-end     | Node 18+, Express 4, TypeScript (native ESM), joi                     |
| Database     | PostgreSQL via Prisma 3                                               |
| Tests        | Jest + supertest (API), Cypress 10 (E2E)                              |

### Screens

- **home** (`/`) - the 10 most recent recommendations, plus the create form.
- **top** (`/top`) - the 10 highest scored recommendations.
- **random** (`/random`) - one recommendation, weighted so that 70% of the time
  it comes from songs scoring above 10.

### API

| Method   | Route                            | Behaviour                                                |
| -------- | -------------------------------- | -------------------------------------------------------- |
| `GET`    | `/health`                        | `{ "status": "ok" }` - liveness probe                    |
| `POST`   | `/recommendations`               | `201`; `409` on duplicate name, `422` on invalid payload |
| `GET`    | `/recommendations`               | 10 most recent, newest first                             |
| `GET`    | `/recommendations/random`        | one weighted-random song; `404` when the table is empty  |
| `GET`    | `/recommendations/top/:amount`   | highest scored first; `422` on a non-positive `:amount`  |
| `GET`    | `/recommendations/:id`           | one song; `404` when unknown or non-numeric              |
| `POST`   | `/recommendations/:id/upvote`    | `+1`; `404` when unknown                                 |
| `POST`   | `/recommendations/:id/downvote`  | `-1`, deletes the row below `-5`; `404` when unknown     |
| `DELETE` | `/tests/reset`                   | truncates the table - **only mounted when `MODE=TEST`**   |

### Layout

```text
.
├── back-end/           Express + Prisma API
│   ├── prisma/         schema, migrations, seed script
│   ├── src/            routers -> controllers -> services -> repositories
│   └── tests/          jest unit + integration suites
├── front-end/          Create React App client
│   ├── cypress/        E2E specs, custom commands, shared helpers
│   └── src/            pages, components, hooks, api services
├── scripts/            first-boot SQL for the local database container
├── docker-compose.yml  local PostgreSQL (dev + test databases)
└── render.yaml         Render blueprint (API + static site + database)
```

## Setup

Requires **Node 18+** and a **PostgreSQL 14+** instance.

### 1. Database

```bash
docker compose up -d
```

This starts PostgreSQL on `localhost:5432` and creates both `singmeasong` and
`singmeasong_test`. Already running your own PostgreSQL? Skip this and create the
two databases yourself.

### 2. Back-end

```bash
cd back-end
npm install
cp .env.example .env
cp .env.example .env.test     # then point it at singmeasong_test and set MODE=TEST
npm run migrate:deploy
npm run seed                  # optional - five songs to look at
npm run dev
```

The API listens on http://localhost:5000.

### 3. Front-end

```bash
cd front-end
npm install
cp .env.example .env
npm start
```

The app opens on http://localhost:3000.

## Environment variables

**Never commit real `.env` files.** Both packages gitignore `.env*` while
tracking `.env.example`, and no credential is committed anywhere in this branch.

### `back-end/.env` - see [`back-end/.env.example`](back-end/.env.example)

| Variable       | Required | Default | Purpose                                                                             |
| -------------- | -------- | ------- | ----------------------------------------------------------------------------------- |
| `DATABASE_URL` | yes      | -       | PostgreSQL connection string used by Prisma                                          |
| `PORT`         | no       | `5000`  | Port the API listens on                                                              |
| `MODE`         | no       | unset   | `TEST` mounts `DELETE /tests/reset`. Leave unset in production                        |
| `CORS_ORIGIN`  | no       | unset   | Comma-separated origin allowlist. When unset, every origin is allowed                |

`back-end/.env.test` takes the same variables and is what `npm test` and the
Cypress suite load. Point it at `singmeasong_test` and set `MODE=TEST`.

### `front-end/.env` - see [`front-end/.env.example`](front-end/.env.example)

| Variable                 | Required | Default                 | Purpose                          |
| ------------------------ | -------- | ----------------------- | -------------------------------- |
| `REACT_APP_API_BASE_URL` | no       | `http://localhost:5000` | Base URL of the API, no trailing slash |

Create React App inlines this at **build** time - changing it requires a rebuild.

## Tests

### API

```bash
cd back-end
npm test                # resets the test database, then unit + integration
npm run test:unit
npm run test:integration
```

**26 passing** (14 unit, 12 integration).

### End-to-end

Cypress drives the real browser against a real API, so both have to be running
and the API needs `MODE=TEST` for `DELETE /tests/reset` to exist.

```bash
# terminal 1 - API against the test database, in test mode
cd back-end && npm run dev:test

# terminal 2 - the app
cd front-end && npm start

# terminal 3
cd front-end && npm run cypress:run
```

**11 passing** across `recommendation.post`, `renderScreen` and `vote.post`.

Override the hosts with `CYPRESS_BASE_URL` and `CYPRESS_API_URL` when either
service runs somewhere other than ports 3000 and 5000.

## Deployment

### Render (blueprint included)

[`render.yaml`](render.yaml) provisions the API, the static front-end and a
managed PostgreSQL instance in one go.

1. Render dashboard → **New** → **Blueprint** → pick this repository and branch.
2. Render creates `singmeasong-db`, `singmeasong-api` and `singmeasong-web`, and
   injects `DATABASE_URL` into the API automatically.
3. Once the API has a URL, set `REACT_APP_API_BASE_URL` on `singmeasong-web` to
   it and redeploy the site - the value is baked into the bundle at build time.
4. Set `CORS_ORIGIN` on `singmeasong-api` to the site's URL to stop other origins
   calling the API.

The API's start command runs `prisma migrate deploy` before booting, so the
schema is applied on every release. `healthCheckPath` is `/health`.

### Any other host

The pieces are ordinary and portable:

```bash
# API - Node service with a PostgreSQL add-on
cd back-end && npm ci && npm run build
npx prisma migrate deploy && npm start        # serves dist/server.js

# Front-end - static bundle behind a SPA fallback
cd front-end && npm ci && REACT_APP_API_BASE_URL=https://your-api npm run build
# publish build/ and rewrite all unknown paths to /index.html
```

The SPA fallback is not optional: without it, refreshing `/top` or `/random`
returns 404 because those paths only exist client-side.

### Deployment status

The repaired build has been verified end to end against the **production
artifacts** - the compiled `dist/server.js` running with a restricted
`CORS_ORIGIN`, and the minified `build/` bundle served behind a SPA fallback -
covering listing, creating, voting, `/top`, `/random`, and a deep-link refresh,
with no console errors.

A **public** deployment has not been created: GitHub Pages is unavailable on this
repository's plan, and every other host in this stack's class requires an account
to be created first. Everything needed to deploy is committed, and the CI
workflow builds both packages on each push so the deployable artifacts stay green.

## Fixes and improvements

Every item below was an actual failure observed while running the project.

### The API could not start at all

- `testController.ts` and `testService.ts` imported their dependencies without
  the `.js` extension. Because `app.ts` statically imports `testRouter`, the
  resulting `ERR_MODULE_NOT_FOUND` crashed the process on **every** start.
- `ts-node` 10.7 cannot register its ESM loader on Node ≥ 18.19, so
  `nodemon src/server.ts` died with `ERR_UNKNOWN_FILE_EXTENSION`. Bumped to
  10.9.2 and made the dev script invoke the loader explicitly, which also fixes
  nodemon failing to resolve the local `ts-node` binary on Windows.
- `tsconfig.json` declared no `target`, so TypeScript defaulted to ES3 and
  emitted invalid output for an ESM package.

### Configuration

- Nothing ever called dotenv, so `PORT` and `MODE` were always undefined at
  runtime - which is why `DELETE /tests/reset` was never mounted and the whole
  E2E suite had nothing to reset against.
- `back-end/.env.example` did not exist; there was no way to discover that
  `DATABASE_URL` was required.
- `front-end/.env.example` shipped `REACT_APP_API_BASE_URL=http://`, not a usable
  base URL. axios resolved every call against the CRA dev server and 404'd.
- `npm start` pointed at `dist/index.js`, a file the compiler never produces, and
  there was no `build` script to produce anything.
- `prisma migrate reset` had no `--force`, so `npm test` blocked forever on an
  interactive prompt; dotenv-cli calls were missing `--`, so flags like
  `--skip-seed` were swallowed before reaching prisma; and `NODE_OPTIONS=... cmd`
  is not valid Windows shell syntax despite `cross-env` already being installed.
- `package.json` declared a `prisma.seed` entry pointing at a `prisma/seed.ts`
  that did not exist.

### Runtime behaviour

- `GET /recommendations/abc` and `/recommendations/top/abc` passed `NaN` to
  Prisma and surfaced as HTTP 500. They now answer 404 and 422.
- `/random` sat on "Loading..." forever whenever the API answered 404 - which it
  does on an empty database - because the page only ever checked for data.
- Added `GET /health` and an optional `CORS_ORIGIN` allowlist (unset keeps the
  previous allow-all behaviour).

### Builds

- `npm run build` failed on **any** host that sets `CI=true` - Vercel, Netlify,
  Render, GitHub Actions all do. `App.js` imported an unused `Component`, and
  react-scripts promotes that warning to an error under CI.

### Tests

Neither jest suite could load, and not one Cypress spec ran.

- The test factory called `require("random-youtube-music-video")` - `require` is
  undefined in an ESM package, and that dependency was never declared.
- Four `expect(...).rejects` assertions were missing `await`, so they passed
  regardless of what the service did.
- A `mockResolvedValueOnce` on `findAll` did not cover the second call
  `getRandom` makes, so the test escaped to the real database.
- The integration suite asserted a list order the repository does not produce,
  and read a new row's id from a `201` response that has no body - upvoting
  `/recommendations/undefined/upvote` and then asserting an accidental tie-break.
- `scenariosFactory.ts` exported none of its four helpers, so it could not be
  imported at all.
- Three of the four Cypress specs were named `*.tests.js`, which the default
  `specPattern` never matches; all three imported a `utils/setup.js` that was
  never committed; `cy.resetData()` called `/reset` instead of `/tests/reset`;
  and `resetPosts`, `createPost` and `seedDatabase` were used but never defined.
- The `data-identifier` attributes every spec selects on did not exist in the
  `Recommendation` component.
- Individual spec bugs: undefined identifiers, an undefined `musicData`, an
  off-by-one in a downvote loop, a "create 15 posts" test that built every song
  with an invalid link so nothing was ever created, and vote assertions aliased
  to an element that stops resolving the moment the score changes.

### Developer setup

- `docker-compose.yml` starts PostgreSQL and creates both databases on first boot.
- `render.yaml` describes the whole deployment.
- A CI workflow runs both jest suites against a real PostgreSQL service container
  and builds the front-end with `CI=true` - the exact setting that caught the
  build failure above.
- Removed `react-player` (a front-end library) and two deprecated `@types` stubs
  from the API's dependencies.

## Known limitations and future improvements

- **No public deployment yet.** See [Deployment status](#deployment-status).
- **Dependencies are old.** Prisma 3.13 (current: 7.x), jest 28, TypeScript 4.6,
  Cypress 10, and axios 0.27. Nothing here is broken by it, but security patches
  and modern tooling are a major-version upgrade away.
- **`--loader ts-node/esm` prints an ExperimentalWarning** on every dev start.
  Node ≥ 20.6 prefers `--import` with `register()`; switching would drop Node 18
  support, so it was left as-is.
- **The E2E suite needs three terminals and a `MODE=TEST` API.** A
  `start-server-and-test` wrapper would collapse that into one command, and would
  let Cypress run in CI.
- **`getRandom` fetches candidates and picks in application code.** Fine at this
  size; a single `ORDER BY random() LIMIT 1` scales better.
- **Votes are unauthenticated and unlimited** - anyone can upvote the same song
  any number of times. There is no rate limiting on any route.
- **`GET /recommendations` is capped at 10 with no pagination**, so older
  recommendations are unreachable from the home timeline.
- **No structured logging or error tracking.** The error middleware
  `console.log`s and returns a bare 500.
- **The front-end has no automated component tests** - `npm test` runs the
  untouched CRA scaffold.

## Credits

Original project by
[@ManuDiasCruz](https://github.com/ManuDiasCruz/sing-me-a-song). This branch
repairs it and adds the setup, testing and deployment tooling described above.
