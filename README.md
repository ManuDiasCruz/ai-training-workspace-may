# 🎵 Sing me a Song

Share YouTube song recommendations and let people vote them up or down. Songs
that drop below **-5** are removed automatically.

Imported from [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song)
and repaired on branch **`731-o-eh-singmeasong`**. The upstream project did not
run: the API could not start on any modern Node, the front-end had no usable API
address, and neither test suite could execute a single test. See
[Fixes and improvements](#fixes-and-improvements) for the full list.

> The unrelated 🦜 Parrot Memory Card Game that previously lived at the root of
> this workspace repository is preserved verbatim in
> [PARROT-GAME-README.md](PARROT-GAME-README.md); its `index.html`, `css/`,
> `img/` and `src/` files are untouched.

---

## Table of contents

- [Project overview](#project-overview)
- [Requirements](#requirements)
- [Setup](#setup)
- [Environment variables](#environment-variables)
- [Running the tests](#running-the-tests)
- [Deployment](#deployment)
- [Fixes and improvements](#fixes-and-improvements)
- [Known limitations and future improvements](#known-limitations-and-future-improvements)

---

## Project overview

Two independent applications in one repository:

| Directory    | Stack                                                        | Default port |
| ------------ | ------------------------------------------------------------ | ------------ |
| `back-end/`  | Node 20, Express 4, TypeScript (ESM), Prisma 3, PostgreSQL    | `5000`       |
| `front-end/` | React 18 (Create React App), React Router 6, axios, Cypress   | `3000`       |

### Application flow

```
CreateNewRecommendation ─┐
Recommendation (vote)  ──┤
                         ▼
        hooks/api/* ──► services/recommendations.js ──► services/api.js (axios)
                                                              │
                                            REACT_APP_API_BASE_URL
                                                              ▼
                          router ──► controller ──► service ──► repository ──► Prisma ──► PostgreSQL
```

- `Timeline` is the layout route (header + menu + `<Outlet/>`), with three child
  routes: `/` (Home), `/top`, `/random`.
- The back-end is a straight router → controller → service → repository chain.
  Controllers validate input, services hold the rules (name uniqueness, the
  `-5` deletion threshold, the weighted random pick), repositories touch Prisma.
- Errors are thrown as tagged objects (`{ type, message }`) and mapped to status
  codes by `errorHandlerMiddleware`.

### API

| Method   | Route                            | Behaviour                                                             |
| -------- | -------------------------------- | --------------------------------------------------------------------- |
| `GET`    | `/health`                        | Liveness probe: `{ status, mode }`                                     |
| `POST`   | `/recommendations`               | Create. `201`, `409` duplicate name, `422` bad body/link              |
| `GET`    | `/recommendations`               | 10 most recent, newest first                                          |
| `GET`    | `/recommendations/random`        | Weighted random: 70% from score > 10, 30% from score ≤ 10. `404` empty |
| `GET`    | `/recommendations/top/:amount`   | Highest scores first                                                  |
| `GET`    | `/recommendations/:id`           | One recommendation. `404` unknown, `422` non-numeric id                |
| `POST`   | `/recommendations/:id/upvote`    | `+1`                                                                  |
| `POST`   | `/recommendations/:id/downvote`  | `-1`, deletes the row once the score drops below `-5`                  |
| `DELETE` | `/tests/reset`                   | **`MODE=TEST` only.** Truncates the table                             |
| `POST`   | `/tests/seed`                    | **`MODE=TEST` only.** Bulk-inserts `{ amount, highScorePercentage }`   |

`youtubeLink` must match `^(https?://)?(www\.youtube\.com|youtu\.?be)/.+$`.

---

## Requirements

- **Node.js 20+** (18 is the floor; the API cannot run on the Node versions the
  original `ts-node` pin supported)
- **PostgreSQL 12+** running locally, or any hosted PostgreSQL
- **npm 9+**

---

## Setup

### 1. Databases

Two databases are needed — the test suite **truncates** the one it is pointed
at, so it must never be the development one.

```bash
psql -U postgres -c "CREATE DATABASE singmeasong;"
psql -U postgres -c "CREATE DATABASE singmeasong_test;"
```

### 2. Back-end

```bash
cd back-end
npm install
cp .env.example .env
cp .env.example .env.test        # then point DATABASE_URL at singmeasong_test
npx prisma migrate deploy        # creates the recommendations table
npx prisma generate              # generates the Prisma client
npm run dev                      # http://localhost:5000
```

Check it: `curl http://localhost:5000/health` → `{"status":"up","mode":"TEST"}`

### 3. Front-end

```bash
cd front-end
npm install
cp .env.example .env             # REACT_APP_API_BASE_URL=http://localhost:5000
npm start                        # http://localhost:3000
```

### Back-end scripts

| Script                      | What it does                                                        |
| --------------------------- | ------------------------------------------------------------------- |
| `npm run dev`               | nodemon + the ts-node ESM loader, reloads on change                  |
| `npm run build`             | `prisma generate` then `tsc -p tsconfig.build.json` → `dist/`        |
| `npm start`                 | Runs the compiled `dist/server.js` (what production runs)            |
| `npm run prisma:migrate`    | `prisma migrate deploy` against `.env`                               |
| `npm test`                  | Resets the test database, then runs both Jest suites                 |
| `npm run test:unit`         | Unit suite only                                                     |
| `npm run test:integration`  | Integration suite only (does not reset first)                        |

### Front-end scripts

| Script            | What it does                                            |
| ----------------- | ------------------------------------------------------- |
| `npm start`       | CRA dev server                                          |
| `npm run build`   | Production bundle into `build/`                          |
| `npm run cy:open` | Cypress interactive runner                              |
| `npm run cy:run`  | Cypress headless                                        |

---

## Environment variables

**No secrets are committed.** `back-end/.env`, `back-end/.env.test` and
`front-end/.env` are all git-ignored (`.env*` with a `!.env.example` negation);
only the annotated `.env.example` templates are tracked. Use your own local
PostgreSQL password, and set production values through the host's own
environment/secret configuration.

### `back-end/.env` and `back-end/.env.test`

| Variable       | Required | Default       | Notes                                                                                              |
| -------------- | -------- | ------------- | -------------------------------------------------------------------------------------------------- |
| `DATABASE_URL` | **yes**  | —             | `postgresql://USER:PASSWORD@HOST:PORT/DATABASE?schema=public`. **Different database in `.env.test`** |
| `PORT`         | no       | `5000`        | HTTP port                                                                                          |
| `NODE_ENV`     | no       | `development` | `development` / `test` / `production`                                                               |
| `MODE`         | no       | unset         | Exactly `TEST` mounts `/tests/*`. **Required for the Cypress suite. Leave unset in production**     |

### `front-end/.env`

| Variable                 | Required | Default                 | Notes                                                                                     |
| ------------------------ | -------- | ----------------------- | ----------------------------------------------------------------------------------------- |
| `REACT_APP_API_BASE_URL` | no\*     | `http://localhost:5000` | API base URL, no trailing slash. **Inlined at build time** — a change needs a rebuild      |

\* There is a fallback so a fresh clone runs, but a deployed build must set it
explicitly. Anything in a CRA env file ends up readable in the public bundle —
never put a secret there.

### Cypress

| Variable            | Default                 | Notes                                        |
| ------------------- | ----------------------- | -------------------------------------------- |
| `CYPRESS_BASE_URL`  | `http://localhost:3000` | Where the front-end is served                |
| `CYPRESS_API_URL`   | `http://localhost:5000` | API base; must be running with `MODE=TEST`   |

---

## Running the tests

### Back-end — 26 tests, Jest + Supertest

```bash
cd back-end
npm test
```

Resets `.env.test`'s database first. Unit tests mock the repository layer;
integration tests drive the real Express app through Supertest against
PostgreSQL.

### Front-end — 12 tests, Cypress

Needs three things running: PostgreSQL, the API **with `MODE=TEST`**, and the
front-end.

```bash
# terminal 1
cd back-end && npm run dev
# terminal 2
cd front-end && npm start
# terminal 3
cd front-end && npm run cy:run
```

| Spec                            | Covers                                                          |
| ------------------------------- | --------------------------------------------------------------- |
| `recommendation.post.tests.js`  | Create: success, invalid link, empty body, duplicate, 10-row cap |
| `renderScreen.tests.js`         | `/random` and `/top` rendering, ordering, empty states           |
| `vote.post.tests.js`            | Up/downvote, repeated votes, deletion below `-5`                 |

The suite points at whatever `CYPRESS_API_URL` says, so it can also be run
against the production build:

```bash
cd back-end  && npm run build && npm start
cd front-end && npm run build && npx serve -s build -l 3000
cd front-end && npm run cy:run
```

---

## Deployment

### Continuous integration

[`.github/workflows/sing-me-a-song-ci.yml`](.github/workflows/sing-me-a-song-ci.yml)
runs on every push to this branch with a PostgreSQL 16 service container:

1. **api** — `npm ci`, `prisma migrate deploy`, `tsc`, both Jest suites.
2. **web** — production build with `CI=true` (warnings are errors), uploaded as
   an artifact.
3. **e2e** — starts the *compiled* API and the *static production build*, then
   runs Cypress against them. Screenshots are uploaded if it fails.

### API — Render blueprint

[`render.yaml`](render.yaml) describes a free PostgreSQL instance, the API as a
Node web service (health check on `/health`), and the front-end as a static
site with an SPA rewrite. Render dashboard → **New → Blueprint** → pick this
repository and branch. Afterwards set `REACT_APP_API_BASE_URL` on the static
site to the API's public URL and redeploy it, because CRA inlines that value at
build time.

`MODE` is intentionally **not** set for the deployed API, so `/tests/reset` and
`/tests/seed` do not exist in production.

### API — Docker

[`back-end/Dockerfile`](back-end/Dockerfile) is a two-stage build that compiles
TypeScript, installs production dependencies only, applies migrations on boot
and serves `dist/server.js`.

```bash
cd back-end
docker build -t sing-me-a-song-api .
docker run -p 5000:5000 -e DATABASE_URL="postgresql://..." sing-me-a-song-api
```

### Front-end — GitHub Pages

[`.github/workflows/sing-me-a-song-pages.yml`](.github/workflows/sing-me-a-song-pages.yml)
(manual dispatch) builds with the right `PUBLIC_URL`, adds a `404.html` SPA
fallback and publishes into `gh-pages/731-o-eh-singmeasong/` without touching
the other folders on that branch.

> ⚠️ **Not currently live.** GitHub Pages is unavailable for this repository:
> it is **private on the GitHub Free plan**, and the API rejects
> `POST /repos/.../pages` with *"Your current plan does not support GitHub Pages
> for this repository."* Enabling it needs the repository to be made public or
> moved to a paid plan — an owner decision, so it was not changed here. Once
> Pages is enabled, set the repository variable `API_BASE_URL` to the deployed
> API URL and run the workflow.

Any static host works in the meantime — the build in `front-end/build/` is
self-contained. Whatever serves it must rewrite unknown paths to `index.html`,
or `/top` and `/random` will 404 on a hard refresh.

### Verified locally against the production artifacts

The compiled API (`node dist/server.js`, no `ts-node`, environment injected the
way a host does it) plus the static `build/` served by `serve -s`: **12/12
Cypress tests pass**, `/top` and `/random` resolve on direct navigation, and
CORS preflight succeeds cross-origin.

---

## Fixes and improvements

### Back-end

| # | Problem | Fix |
| - | ------- | --- |
| 1 | **API could not start at all.** `npm run dev` ran `nodemon src/server.ts` → plain `ts-node`; with `"type": "module"` Node refuses a `.ts` entrypoint (`ERR_UNKNOWN_FILE_EXTENSION`) | `dev` invokes the ts-node ESM loader |
| 2 | `ts-node` pinned to `^10.7.0`, whose ESM resolver dies on Node ≥ 18.19 with `ERR_LOADER_CHAIN_INCOMPLETE` | Bumped to `^10.9.2` |
| 3 | `testController` / `testService` imported without the mandatory `.js` extension → `ERR_MODULE_NOT_FOUND`, taking down `/tests/*` | Added the extensions |
| 4 | **No `build` script**, and `start` pointed at `dist/index.js`, which the compiler never produced | Added `tsconfig.build.json` + `build`; `start` runs `dist/server.js` |
| 5 | `tsconfig` compiled to ES3 (`target` unset) with `module: es6` | `target`/`module` → `es2020`, `skipLibCheck`, source maps |
| 6 | `dotenv` was a dependency but never imported; `PORT`/`MODE` only worked by accident, via Prisma's own `.env` side effect | `src/config/env.ts`, loaded first in `app.ts` |
| 7 | Non-numeric route params (`/recommendations/abc`) passed `NaN` to Prisma → **500** with a stack trace | Validated in the controller → `422` |
| 8 | Test scripts used POSIX-only inline `NODE_OPTIONS=` and a stray `--` that Jest read as a path filter | Routed through `cross-env` (already a dependency, unused) and fixed the `dotenv-cli` separator |
| 9 | `prisma.seed` pointed at `prisma/seed.ts`, a file that does not exist | Removed |
| 10 | `react-player` (a React library) sat in the API's dependencies | Removed |
| 11 | `back-end/.env.example` did not exist | Added, fully annotated |
| 12 | Every error was logged, so ordinary 404/409/422 responses flooded the logs | Only unexpected errors, via `console.error` |
| 13 | Nothing to health-check a deployment with | Added `GET /health` |

### Front-end

| #  | Problem | Fix |
| -- | ------- | --- |
| 14 | `.env.example` shipped `REACT_APP_API_BASE_URL=http://` — an invalid URL — and no `.env` exists, so axios built **relative** URLs, every request hit the dev server, and every page sat on "Loading..." forever | Real default, trailing-slash normalisation, console warning when unset |
| 15 | A failed request left Home/Top on "Loading..." indefinitely; `useAsync` tracked an `error` nobody read | `ApiError` panel naming the attempted URL, with retry |
| 16 | `/random` was permanently stuck on an empty database (`404`) and after the 6th downvote deleted the song on screen | Falls back to the empty state |
| 17 | **`CI=true npm run build` failed** on an unused `Component` import — CRA promotes warnings to errors, which is the default in Actions and on most hosts | Removed the import |
| 18 | `Top.js` exported a component named `Home` | Renamed |
| 19 | Tab title read "React App"; manifest said "Create React App Sample" | Real name, description and theme colour |

### Tests

| #  | Problem | Fix |
| -- | ------- | --- |
| 20 | **Both Jest suites died before the first test**: the factory called `require("random-youtube-music-video")` — `require` does not exist in ESM, and the package was never in `package.json` | Songs generated locally with faker, matching the link regex |
| 21 | Five `expect(...).rejects` assertions had no `await`, so they could never fail — and the stray rejection crashed the runner with exit 255 while printing "14 passed" | Awaited |
| 22 | "Error notfound in get random" mocked `findAll` once, but `getByScore` calls it twice, so the assertion hit the real database | Both calls mocked |
| 23 | "List recommendations" expected the order `[2, 1, 3]`, which no sort produces (`findAll` is `id desc`) | Corrected to `[3, 2, 1]` |
| 24 | `scenariosFactory.ts` declared four helpers with **no `export`** — dead code — and one discarded the song it generated | Exported, renamed, fixed |
| 25 | **Cypress ran zero project specs**: `specPattern` only matched `*.cy.js` while every real spec is `*.tests.js`; the ~20 CRA example specs ran instead | Widened the pattern, deleted the scaffolding |
| 26 | Three specs imported `./utils/setup.js`, absent from the repository → compile failure | Added it |
| 27 | `cy.resetPosts` / `cy.seedDatabase` / `cy.createPost` were called but never defined; `cy.resetData` hit `/reset` instead of `/tests/reset` | Implemented all of them |
| 28 | No `baseUrl`; `localhost:3000` and `localhost:5000` hardcoded in every spec | `baseUrl` + `apiUrl` from config/env |
| 29 | `spec.recommendation.cy.js` duplicated another spec and referenced undefined `name`/`youtubeLink` | Deleted in favour of the working copy |
| 30 | `vote.post.tests.js` referenced an undefined `musicData`, chained score state across tests via one `before`, and reset the database mid-run | Each test independent |
| 31 | "Add ≥ 10 posts" built its 15 songs with `createWrongLink()`, so every POST was a 422 and nothing was ever created | Valid songs |
| 32 | Specs selected on `cy.get("input").first()` and `cy.contains("0")`, and the `data-identifier` attributes they queried did not exist in the markup | Added the attributes, switched the selectors |
| 33 | `cy.seedDatabase` had no endpoint behind it | Added `POST /tests/seed` (`MODE=TEST` only) |

### Infrastructure

| #  | Added |
| -- | ----- |
| 34 | `.github/workflows/sing-me-a-song-ci.yml` — build + unit + integration + E2E against the production artifacts, with a PostgreSQL service container |
| 35 | `back-end/Dockerfile` + `.dockerignore` — two-stage production image |
| 36 | `render.yaml` — database + API + static site blueprint |
| 37 | `.github/workflows/sing-me-a-song-pages.yml` — front-end → `gh-pages/731-o-eh-singmeasong/` |

---

## Known limitations and future improvements

Tracked as GitHub issues against branch `731-o-eh-singmeasong`.

1. **The front-end is not publicly deployed.** GitHub Pages is unavailable for a
   private repository on the Free plan (see [Deployment](#deployment)). The
   workflow is ready; enabling Pages is an owner decision.
2. **The API has no public deployment either.** `render.yaml` and the Dockerfile
   are ready, but creating the hosting account is the owner's call.
3. **CORS is fully open** (`app.use(cors())`). Fine for an open read/write demo,
   but a real deployment should allow-list its own origin.
4. **No authentication or rate limiting.** Anyone can create recommendations and
   vote without limit; a downvote loop can delete any song.
5. **Votes are not per-user**, so the same person can vote repeatedly.
6. **Dependencies are from 2022** and `npm audit` reports vulnerabilities
   (Prisma 3 → 7, CRA 5 unmaintained, axios 0.27, faker 7). Upgrading is a
   deliberate migration, out of scope for a repair pass.
7. **`GET /recommendations` is capped at 10 rows** with no pagination, so older
   recommendations become unreachable through the UI.
8. **No structured logging or error tracking** — failures only reach stdout.
9. **`react-scripts test` has no tests**; the front-end has no component-level
   coverage, only E2E.
10. **The weighted random pick loads a bucket and picks in JS**, which will not
    scale; it belongs in SQL.

---

## Credits

Original project by [ManuDiasCruz](https://github.com/ManuDiasCruz)
([sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song)). The
front-end's original Create React App notes are kept in
[front-end/README.md](front-end/README.md).
