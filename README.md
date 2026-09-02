# 🎵 Sing me a Song

Share song recommendations and let people vote them up or down. Anyone can post
a YouTube link, upvote what they like, and downvote what they don't — a
recommendation that falls below **-5** is removed automatically.

Three views:

| View | Route | What it shows |
| --- | --- | --- |
| Home | `/` | The 10 most recent recommendations |
| Top | `/top` | The 10 highest-scoring recommendations |
| Random | `/random` | One recommendation, weighted towards high scores |

The random view is deliberately biased: 70% of the time it picks from songs
scoring **above 10**, and 30% of the time from songs scoring **10 or below**.
When the chosen bucket is empty it falls back to the whole catalogue.

---

## Stack

**Back end** — Node.js + Express (native ESM), TypeScript, Prisma ORM,
PostgreSQL, joi for validation, Jest + Supertest for tests.

**Front end** — React 18 (Create React App), React Router 6, axios,
styled-components, `react-player` for embedded YouTube, Cypress for
end-to-end tests.

```
back-end/
  prisma/            Prisma schema + migrations
  src/
    routers/         Route definitions
    controllers/     Request/response handling and param validation
    services/        Business rules (scoring, the random algorithm)
    repositories/    Prisma queries
    middlewares/     Central error handler
    utils/           AppError types -> HTTP status mapping
  tests/
    unit/            Service layer, repository fully mocked
    integration/     Full HTTP round-trips via Supertest
front-end/
  src/
    pages/           Timeline layout + Home / Top / Random
    components/      Header, Menu, Recommendation, CreateNewRecommendation
    hooks/api/       One hook per endpoint, all over useAsync
    services/        axios instance + endpoint functions
  cypress/e2e/       End-to-end specs
render.yaml          Render Blueprint for a one-click deploy
```

Errors travel as `AppError` objects (`conflict`, `not_found`, `unauthorized`,
`wrong_schema`) and `errorHandlerMiddleware` maps them to 409 / 404 / 401 / 422.

---

## API

Base URL: `http://localhost:5000` in development.

| Method | Route | Body | Success | Errors |
| --- | --- | --- | --- | --- |
| `POST` | `/recommendations` | `{ name, youtubeLink }` | `201` | `422` invalid body, `409` duplicate name |
| `GET` | `/recommendations` | — | `200` (≤10, newest first) | — |
| `GET` | `/recommendations/random` | — | `200` | `404` when empty |
| `GET` | `/recommendations/top/:amount` | — | `200` (by score desc) | `422` non-numeric amount |
| `GET` | `/recommendations/:id` | — | `200` | `404`, `422` non-numeric id |
| `POST` | `/recommendations/:id/upvote` | — | `200` | `404`, `422` non-numeric id |
| `POST` | `/recommendations/:id/downvote` | — | `200` | `404`, `422` non-numeric id |

`name` must be unique and `youtubeLink` must match
`^(https?://)?(www\.youtube\.com|youtu\.?be)/.+$`.

### Test-only routes

Mounted **only** when the API runs with `MODE=TEST`. They exist for the Cypress
suite and can wipe the database, so never enable `MODE` in production.

| Method | Route | Body |
| --- | --- | --- |
| `DELETE` | `/tests/reset` | — (truncates and restarts identity) |
| `POST` | `/tests/seed` | `{ amount, highScorePercentage }` |

---

## Requirements

- **Node.js 18+** (developed and verified on 20.18) — the back end uses native
  ESM with the ts-node ESM loader, which needs a modern Node.
- **PostgreSQL 12+** (verified on 16)
- npm 8+

---

## Environment variables

Never commit real values: `.env*` is gitignored in both packages (with
`.env.example` explicitly allowed through).

### `back-end/.env` — see [`back-end/.env.example`](back-end/.env.example)

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | Prisma connection string, e.g. `postgresql://user:pass@localhost:5432/singmeasong?schema=public` |
| `PORT` | no | API port, defaults to `5000` |
| `MODE` | no | Set to `TEST` to mount the `/tests` helper routes. Leave unset in production. |

### `back-end/.env.test`

Same variables, but **point `DATABASE_URL` at a different database** — the test
scripts reset it on every run — and set `MODE=TEST`.

### `front-end/.env` — see [`front-end/.env.example`](front-end/.env.example)

| Variable | Required | Description |
| --- | --- | --- |
| `REACT_APP_API_BASE_URL` | recommended | API base URL, no trailing slash. Falls back to `http://localhost:5000` with a console warning. |

> Create React App only exposes variables prefixed with `REACT_APP_`, and it
> **inlines them at build time** — rebuild after changing this value.

---

## Local setup

### 1. Create the databases

```bash
createdb singmeasong && createdb singmeasong_test
```

Or from `psql`:

```bash
psql -U postgres -c "CREATE DATABASE singmeasong;" -c "CREATE DATABASE singmeasong_test;"
```

### 2. Back end

```bash
cd back-end
npm install
cp .env.example .env
```

Edit `.env` with your `DATABASE_URL`, then create `.env.test` with the *test*
database and `MODE=TEST`. Apply the schema and start:

```bash
npx prisma migrate deploy
npm run dev
```

The API listens on <http://localhost:5000>.

### 3. Front end

```bash
cd front-end
npm install
cp .env.example .env
npm start
```

The app opens at <http://localhost:3000>.

### Back-end scripts

| Script | What it does |
| --- | --- |
| `npm run dev` | Watch mode via nodemon + the ts-node ESM loader |
| `npm run build` | `prisma generate` then `tsc` into `dist/` |
| `npm start` | Runs the compiled `dist/server.js` |
| `npm run prisma:migrate` | `prisma migrate deploy` |
| `npm test` | Resets the test database, then runs unit + integration |
| `npm run test:unit` | Unit tests only |
| `npm run test:integration` | Integration tests only (resets the test DB first) |

### Front-end scripts

| Script | What it does |
| --- | --- |
| `npm start` | CRA dev server |
| `npm run build` | Production bundle into `build/` |
| `npm run cypress:open` | Cypress interactive runner |
| `npm run cypress:run` | Cypress headless run |

---

## Tests

### Back end — 26 tests

```bash
cd back-end
npm test
```

### Front end — 12 end-to-end tests

Cypress drives the real UI against the real API, so three things must be
running: PostgreSQL, the API **with `MODE=TEST`**, and the front end.

```bash
# terminal 1 — API with the test routes mounted
cd back-end && npm run dev:test

# terminal 2 — front end
cd front-end && npm start

# terminal 3
cd front-end && npm run cypress:run
```

The suite resets the database between tests, so point the API at your **test**
database while running it.

To run the suite against a deployed environment:

```bash
CYPRESS_BASE_URL=https://your-frontend CYPRESS_API_URL=https://your-api npm run cypress:run
```

---

## Deployment

[`render.yaml`](render.yaml) is a [Render Blueprint](https://render.com/docs/infrastructure-as-code)
describing all three resources — a free PostgreSQL instance, the API as a Node
web service, and the front end as a static site.

In the Render dashboard: **New → Blueprint**, pick this repository and this
branch. Render wires the connections itself:

- `DATABASE_URL` comes from the managed database (`fromDatabase`), so no
  credentials are ever written into the repository.
- The front-end build reads the API hostname through `fromService` and inlines
  `REACT_APP_API_BASE_URL` at build time.
- `prisma migrate deploy` runs in the API build step; it is idempotent, so
  redeploys are safe.
- `MODE` is deliberately left unset so the destructive `/tests` routes stay
  unmounted.

Client-side routing is handled by a rewrite of `/*` to `/index.html`, so
`/top` and `/random` survive a page refresh.

### Any other host

The build outputs are ordinary and portable:

```bash
# API
cd back-end && npm ci && npm run build && npx prisma migrate deploy && npm start

# Front end — serve the static bundle behind an SPA fallback
cd front-end && npm ci && REACT_APP_API_BASE_URL=https://your-api npm run build
```

The API reads `PORT` from the environment, which is what most platforms inject.
CORS is currently open to all origins (see *Known limitations*).

### Deployment status

**Not deployed yet.** No hosting account is connected to this repository and
the repository is private, so GitHub Pages would have made the build public.
What *has* been verified is the exact production artifacts, locally: the
compiled API (`node dist/server.js`, no `MODE`) behind the static production
bundle served on a separate origin. Create, upvote, downvote, `/top`, `/random`,
CORS preflight and deep-link refreshes all behaved correctly, and the `/tests`
routes correctly returned 404. The live deploy is tracked in
[#560](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/560).

---

## What was repaired

The project did not run at all when this branch started. Neither package could
boot and no test suite could execute.

### Back end could not start

- `npm run dev` ran `nodemon src/server.ts`, but `package.json` declares
  `"type": "module"`, so ts-node needs its ESM loader. On top of that
  **ts-node 10.7 predates Node 20's ESM hook API** and failed with
  `ERR_UNKNOWN_FILE_EXTENSION` for every `.ts` file. Bumped to `^10.9.2` and
  run nodemon through `node --loader ts-node/esm`.
- `testController.ts` and `testService.ts` imported their dependencies
  **without the mandatory `.js` extension**. Since `app.ts` imports the test
  router unconditionally, the server crashed with `ERR_MODULE_NOT_FOUND` on
  startup in *every* mode.
- `npm start` pointed at `dist/index.js`, which no build ever produced, and
  there was **no build script at all**. Added `build` and pointed
  `start`/`main` at `dist/server.js`.
- `tsconfig.json` had no `include`, so `tsc` pulled the tests into `dist/` and
  shifted the output paths; `target` was unset (defaulting to ES3). Scoped it
  to `src/` with `rootDir`/`outDir` and pinned `target`/`lib` to ES2020.
- `server.ts` never loaded dotenv, so `PORT` and `MODE` from `.env` were
  ignored.
- `package.json` declared a Prisma seed at `prisma/seed.ts`, a file that does
  not exist.
- `prisma migrate reset` prompts for confirmation, so `npm test` could never
  run unattended. Added `--force`, and routed `NODE_OPTIONS` through the
  already-installed `cross-env` so the scripts also work on Windows.

### Back-end tests could not run

- `jest.config.js` used the plain `ts-jest` preset, which **emits CommonJS
  while Node links the files as ESM** — every suite died with
  `ReferenceError: exports is not defined`. The ESM preset
  (`ts-jest/presets/default-esm`) fixes it.
- `test:unit` and `test:integration` omitted the
  `NODE_OPTIONS=--experimental-vm-modules` that `test` had, so they failed
  even earlier, on `Cannot destructure property 'PrismaClient'`.
- The song factory called `require()` **inside an ES module**, and did so for
  `random-youtube-music-video` — a package **never listed in
  `package.json`**. It also never awaited the async generator, so
  `youtubeLink` was a pending Promise rather than a URL. Songs are now
  generated locally with faker, which keeps the suite hermetic and produces
  links that satisfy the joi pattern.
- `"List recommendations"` asserted an order the repository never produces
  (`findAll` orders by `id desc`, newest first).
- `"List top recommendations"` read the created id from the POST response, but
  POST answers `201` with an **empty body**. It upvoted
  `/recommendations/undefined/upvote` and only passed because all three scores
  stayed `0` — it never tested what it claimed.
- Five `expect(...).rejects` assertions were **never awaited**, so they could
  not fail. The random "not found" case also mocked `findAll` only once and
  silently queried the real database through the fallback path.

### Front-end / back-end integration was broken

- `front-end/.env.example` shipped the truncated value
  `REACT_APP_API_BASE_URL=http://`, so copying it produced an unusable axios
  `baseURL`. With the variable missing entirely, axios falls back to a relative
  URL and every request hits the CRA dev server
  (`localhost:3000/recommendations` → 404) — which reads as a broken app rather
  than missing configuration. `api.js` now falls back to `http://localhost:5000`
  and warns.
- Non-numeric route params (`/recommendations/abc`, `/top/abc`,
  `/abc/upvote`) were coerced with `+id`, handed `NaN` to Prisma and surfaced
  the driver error as a **500**. They now return `422`.

### The end-to-end suite had never executed

- Three of the four specs were named `*.tests.js`, which the default `*.cy.js`
  `specPattern` never matches, so Cypress simply skipped them.
- All three imported `./utils/setup.js` — **a file that does not exist in the
  repository** — so they would have failed on import anyway.
- `cy.resetPosts`, `cy.createPost` and `cy.seedDatabase` were used but never
  defined; only `resetData` and `addSong` existed.
- `cy.resetData` called `DELETE /reset`, but the route is `/tests/reset`.
- No component rendered the `data-identifier` attributes the specs select on
  (`upvote`, `downvote`, `vote-menu`), so every selector missed.
- Scores cannot be set through the public API, so the "top" and "random"
  scenarios had no way to build a ranked catalogue. Added a test-only
  `POST /tests/seed`.
- `vote.post` referenced an undefined `musicData` and chained its tests through
  shared score state; the "show only 10 posts" case posted **invalid** links, so
  the API answered 422 every time and nothing was ever rendered to count.
- The API host was hardcoded in `commands.js` and in every `cy.visit`, so the
  suite could only run against localhost. Both now come from `cypress.config.js`
  and can be overridden, which is what lets the suite run against a deployment.
- Removed `spec.recommendation.cy.js`, a superseded draft that called an async
  factory without awaiting it and typed undefined globals, plus the Cypress
  scaffolding examples under `1-getting-started` / `2-advanced-examples`, which
  exercise `example.cypress.io` rather than this app and made `cypress run`
  fail.

### Housekeeping

- `App.js` imported React's `Component` but shadowed it with the `LazyWrapper`
  parameter — dead code that produced a build warning.
- The page title, description and PWA manifest still said "React App" /
  "Create React App Sample".
- `<Router>` now takes `basename={process.env.PUBLIC_URL}` so the bundle also
  works when served from a sub-path.

### Result

| Suite | Before | After |
| --- | --- | --- |
| Back-end unit | could not run | **14 passing** |
| Back-end integration | could not run | **12 passing** |
| Cypress end-to-end | never discovered | **12 passing** |

---

## Known limitations and future improvements

Each of these has a tracking issue.

- [#560](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/560)
  — **Not deployed yet.** Needs a hosting account to be connected; see
  *Deployment status* above.
- [#561](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/561)
  — **CORS is wide open.** `app.use(cors())` allows every origin. Production
  should restrict it to the front-end origin via an env var.
- [#562](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/562)
  — **`POST /recommendations` returns an empty 201.** Clients cannot learn the
  id of what they just created without a follow-up query — this is what made
  one integration test silently vote on `undefined`.
- [#563](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/563)
  — **`GET /recommendations` hard-codes `take: 10`** with no pagination, so
  older recommendations are unreachable. It also skews `/random`, which filters
  through the same query.
- [#564](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/564)
  — **Dependencies are from 2022** and `npm audit` reports 31 vulnerabilities in
  the back end. React Scripts 5 / Prisma 3 / Jest 28 all have newer majors, and
  the ESM + `--experimental-vm-modules` Jest setup would get simpler with them.
- [#565](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/565)
  — **No CI.** Nothing runs the three suites automatically on push, which is how
  the repository reached a state where none of them could execute.
- [#566](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/566)
  — **Dead code.** `react-player` is a back-end dependency despite being a React
  package used only by the front end, and `tests/factories/scenariosFactory.ts`
  is imported by nothing.
- [#567](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/567)
  — **The `/random` view re-fetches the same song after voting** rather than
  drawing a new one, and if a downvote deletes it the stale card stays on screen
  because the failed request leaves the previous data in place.

Not yet tracked: the error handler logs raw errors with `console.log` and
returns bare strings rather than structured JSON.

---

## Original front-end documentation

The Create React App reference that shipped with the project is preserved at
[`front-end/README.md`](front-end/README.md).
