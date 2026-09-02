# Sing me a Song

A full-stack app for anonymous song recommendations. Anyone can post a YouTube
link with a name, upvote or downvote it, browse the newest recommendations, see
the top-rated ones or ask for a random pick. Recommendations whose score drops
below -5 are removed automatically.

Original project: <https://github.com/ManuDiasCruz/sing-me-a-song>. This
branch (`0827-feh-singasong`) contains the repaired, deployable version. The
original Create React App notes are preserved in
[`front-end/README.md`](front-end/README.md).

| Layer     | Stack                                                                    |
| --------- | ------------------------------------------------------------------------ |
| Front-end | React 18 (Create React App), react-router 6, styled-components, react-player, Cypress 10 |
| Back-end  | Node.js 18+, Express 4, TypeScript (ESM), Prisma 3, Joi, Jest 28 + Supertest |
| Database  | PostgreSQL                                                               |

## Project structure

```
.
├── back-end/            # REST API
│   ├── prisma/          # schema + migrations
│   ├── src/             # app.ts (Express app), server.ts (entry point)
│   │   ├── routers/ controllers/ services/ repositories/
│   │   ├── schemas/     # Joi validation
│   │   └── middlewares/ utils/
│   └── tests/           # unit + integration (Jest)
├── front-end/           # React SPA
│   ├── src/             # pages/, components/, hooks/, services/
│   └── cypress/         # E2E tests
├── render.yaml          # Render Blueprint (API + PostgreSQL)
└── .github/workflows/   # CI and GitHub Pages deployment
```

## Application flow

1. **Home** (`/`) lists the 10 newest recommendations and has the form to add
   one (`POST /recommendations`, name must be unique, link must be a YouTube URL).
2. Each card embeds the YouTube player and has up/down arrows
   (`POST /recommendations/:id/upvote|downvote`). A downvote that takes the score
   below -5 deletes the recommendation.
3. **Top** (`/top`) shows the 10 highest-scored recommendations
   (`GET /recommendations/top/10`).
4. **Random** (`/random`) shows one recommendation (`GET /recommendations/random`):
   70% of the time one with score > 10, otherwise one with score <= 10, falling
   back to any recommendation when the chosen bucket is empty.

## Prerequisites

- Node.js 18 or newer (tested with 20.18) and npm
- A PostgreSQL server (local install, Docker, or a hosted instance)

## Setup

### 1. Back-end

```bash
cd back-end
npm install
cp .env.example .env          # edit DATABASE_URL if needed
npx prisma migrate deploy     # creates the recommendations table
npm run dev                   # http://localhost:5000
```

Useful scripts:

| Script                   | What it does                                                     |
| ------------------------ | ---------------------------------------------------------------- |
| `npm run dev`            | Dev server with reload (`tsx watch`)                             |
| `npm run build`          | Generates the Prisma client and compiles TypeScript to `dist/`   |
| `npm start`              | Runs the compiled server (`node dist/server.js`)                 |
| `npm run migrate:deploy` | Applies pending migrations (use in production)                   |
| `npm test`               | Resets the **test** database, then runs unit + integration tests |
| `npm run test:unit` / `npm run test:integration` | Runs one suite (test DB must already be migrated) |
| `npm run dev:test`       | Migrates the test DB and starts the API with `MODE=TEST` (for Cypress) |

Tests need `back-end/.env.test` (copy `.env.test.example`). Point it at a
**throwaway** database: the suite truncates and resets it.

### 2. Front-end

```bash
cd front-end
npm install
cp .env.example .env          # REACT_APP_API_BASE_URL=http://localhost:5000
npm start                     # http://localhost:3000
```

`npm run build` produces the static bundle in `front-end/build`.

### 3. End-to-end tests (Cypress)

Cypress drives the real front-end against the real API, so both must be running
and the API must run in test mode (it exposes `DELETE /tests/reset` and
`POST /tests/seed`, which the specs use to prepare data):

```bash
# terminal 1
cd back-end && npm run dev:test
# terminal 2
cd front-end && npm start
# terminal 3
cd front-end && npx cypress run          # or: npx cypress open
```

Override the targets with `CYPRESS_BASE_URL` (front-end) and `CYPRESS_apiUrl`
(API) if you use different ports.

## Environment variables

### Back-end (`back-end/.env`, see `.env.example`)

| Variable       | Required | Description                                                                 |
| -------------- | -------- | --------------------------------------------------------------------------- |
| `DATABASE_URL` | yes      | PostgreSQL connection string used by Prisma                                 |
| `PORT`         | no       | HTTP port (default `5000`)                                                  |
| `MODE`         | no       | Set to `TEST` to mount the `/tests` router (reset/seed helpers). **Never set it in production.** |

`back-end/.env.test` (see `.env.test.example`) uses the same variables and is
loaded by the test scripts.

### Front-end (`front-end/.env`, see `.env.example`)

| Variable                  | Required | Description                                           |
| ------------------------- | -------- | ----------------------------------------------------- |
| `REACT_APP_API_BASE_URL`  | yes      | Base URL of the API, no trailing slash. Baked in at build time. |
| `PUBLIC_URL`              | no       | Sub-path the app is served from (set automatically by the Pages workflow) |

### GitHub Actions

| Where                              | Name                     | Description                                    |
| ---------------------------------- | ------------------------ | ---------------------------------------------- |
| Repository **variable** (Settings → Secrets and variables → Actions) | `REACT_APP_API_BASE_URL` | Public URL of the deployed API, used only by the (manual) GitHub Pages workflow |

The Render Blueprint needs no variables or secrets: `DATABASE_URL` is injected
by Render and the front-end uses the relative `/api` base URL.

No secrets are committed. `.env*` files are ignored by git; only the
`*.example` files are tracked.

## API reference

| Method | Path                            | Description                                   | Responses           |
| ------ | ------------------------------- | --------------------------------------------- | ------------------- |
| GET    | `/health`                       | Liveness check                                | 200 `{status:"ok"}` |
| POST   | `/recommendations`              | Create `{ name, youtubeLink }`                | 201, 409 duplicate name, 422 invalid body |
| GET    | `/recommendations`              | 10 newest recommendations                     | 200                 |
| GET    | `/recommendations/random`       | One recommendation (score-weighted)           | 200, 404 when empty |
| GET    | `/recommendations/top/:amount`  | `amount` highest-scored recommendations       | 200, 422 bad amount |
| GET    | `/recommendations/:id`          | One recommendation                            | 200, 404, 422 bad id |
| POST   | `/recommendations/:id/upvote`   | score + 1                                     | 200, 404, 422       |
| POST   | `/recommendations/:id/downvote` | score - 1; deletes when score < -5            | 200, 404, 422       |
| DELETE | `/tests/reset`                  | Truncate table (**`MODE=TEST` only**)         | 200                 |
| POST   | `/tests/seed`                   | Bulk insert `{ amount, highScorePercentage }` (**`MODE=TEST` only**) | 201 |

## Deployment

The front-end is a static bundle and the API is a long-running Node process
that needs PostgreSQL. [`render.yaml`](render.yaml) is a Render Blueprint that
deploys all three pieces on the free tier in one step (this repository already
had Render deployments in the past, so the Render GitHub app is installed).

### Render Blueprint (API + PostgreSQL + static front-end)

1. Render dashboard → **New → Blueprint** → pick this repository → branch
   `0827-feh-singasong` → **Apply**.
2. Render creates:
   - `sing-me-a-song-feh-db` — free PostgreSQL instance.
   - `sing-me-a-song-feh-api` — Node web service from `back-end/`, built with
     `npm ci && npm run build`, started with
     `npx prisma migrate deploy && npm start`, health-checked on `/health`,
     `DATABASE_URL` injected from the database.
   - `sing-me-a-song-feh` — static site from `front-end/` (`npm run build`,
     publishes `build/`). It is built with `REACT_APP_API_BASE_URL=/api` and a
     rewrite rule proxies `/api/*` to the API service, so the browser talks to
     a single origin (no CORS) and the API URL never has to be baked in.
     A second rewrite (`/* → /index.html`) makes `/top` and `/random`
     refresh-safe.
3. Open `https://sing-me-a-song-feh.onrender.com`. If Render had to rename the
   API service because the name was taken, edit the `/api/*` rewrite destination
   (in `render.yaml` or in the static site's *Redirects/Rewrites* settings).

Any other Node host works the same way: set `DATABASE_URL`, run
`npm ci && npm run build`, then `npx prisma migrate deploy && npm start`
inside `back-end/`. For the front-end, build with `REACT_APP_API_BASE_URL`
pointing at the public API URL and serve `front-end/build` as a static site
with an SPA fallback. Do **not** set `MODE=TEST` in production.

### GitHub Pages (front-end only, manual)

`.github/workflows/deploy-frontend.yml` can publish the front-end to GitHub
Pages, but Pages is **not available for private repositories on the free GitHub
plan** (the API answers "Your current plan does not support GitHub Pages"), so
the workflow is manual-only (`workflow_dispatch`). To use it: make the
repository public or upgrade the plan, enable *Settings → Pages → Source:
GitHub Actions*, set the repository variable `REACT_APP_API_BASE_URL` to the
public API URL and run the workflow. The build sets `PUBLIC_URL` to the
repository sub-path (the router uses it as `basename`) and copies `index.html`
to `404.html` for deep links.

## Fixes and improvements in this branch

Back-end

- The dev server did not start: `ts-node` fails with
  `ERR_UNKNOWN_FILE_EXTENSION` on Node 20 in ESM mode, and two imports lacked
  the `.js` extension required by Node ESM. Switched dev scripts to `tsx` and
  fixed the imports.
- There was no build; `npm start` pointed at a non-existent `dist/index.js`.
  Added `npm run build` (tsc → `dist/`) and a working `start`.
- Test scripts were Unix-only (`NODE_OPTIONS=...` inline) and interactive
  (`prisma migrate reset` without `--force`); fixed with `cross-env`/`--force`.
- `.env` was only read by Prisma; `PORT`/`MODE` were ignored. `dotenv/config`
  is now loaded at startup.
- Removed the unused `react-player` dependency and a Prisma seed config that
  pointed to a missing file; added `.env.example` / `.env.test.example`.
- Added `GET /health`, validation of `:id`/`:amount` (422 instead of a Prisma
  500), and Joi's message in 422 responses.
- Test suite: the factory required an unlisted package
  (`random-youtube-music-video`); unit tests never awaited `rejects` and leaked
  spies between tests; two integration tests asserted the wrong order / used an
  empty response body as an id. All 35 tests now pass.
- Added `POST /tests/seed` (test mode only) for the Cypress suite.

Front-end

- Production build failed on every CI (`CI=true` turns the unused
  `Component` import warning into an error).
- `/random` hung on "Loading..." for an empty database and kept showing a
  recommendation that had just been deleted; it now shows an empty state and
  loads another one.
- Router honours `PUBLIC_URL` (sub-path hosting); real page title/manifest.
- Cypress: reset command pointed at a non-existent `/reset` route; specs
  referenced undefined variables, missing commands (`resetPosts`, `createPost`,
  `seedDatabase`), a missing `utils/setup.js`, wrong expected scores and were
  named `*.tests.js` so Cypress never ran them. Rewritten and renamed to
  `*.cy.js`; the Cypress example scaffolding was removed.

Project

- CI workflow (API tests with PostgreSQL + front-end build), GitHub Pages
  deployment workflow, Render Blueprint, root `.gitignore`, this README.

## Known limitations and future improvements

- Applying the Render Blueprint requires access to the Render account; no
  hosting credentials were available in the environment where this branch was
  prepared, so the blueprint was validated locally (build/start/migrate
  commands, health check) but not applied yet.
- Render's free plan sleeps after inactivity (first request is slow) and free
  PostgreSQL instances expire after 30 days.
- GitHub Pages cannot be used while the repository is private on the free plan.
- CORS is open to any origin and voting is anonymous and unlimited.
- Prisma 3 and Create React App are end-of-life; upgrading (Prisma 5+/6, Vite)
  is the next maintenance step.
- Cypress runs locally only; it is not part of CI yet.
- Home/Top show at most 10 items with no pagination; errors use `alert()`.
