# 🎵 Sing me a Song

A song-recommendation timeline: anyone can post a YouTube link, and the
community pushes it up or down. Recommendations that fall below **-5** are
deleted automatically, and the *random* page is biased towards the songs
people actually like.

Imported from [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song)
and repaired on branch **`723-oeh-singmeasong`**.

> The previous occupant of this file, the **Parrot Memory Card Game** README,
> is preserved verbatim at [`docs/parrot-memory-card-game.md`](docs/parrot-memory-card-game.md).
> The Create React App boilerplate notes are still at
> [`front-end/README.md`](front-end/README.md).

---

## Live deployment

| Piece | Status | URL |
| --- | --- | --- |
| Front-end | **Deployed** | <https://manudiascruz.github.io/sing-me-a-song-deploy/> |
| API | **Not hosted** — blueprint provided | see [Deploying](#deploying) |

The published bundle is built with `REACT_APP_API_BASE_URL` unset, so it falls
back to `http://localhost:5000`. Start the API locally (see
[Running locally](#running-locally)) and the deployed page works end to end;
browsers exempt `localhost` from mixed-content blocking. If the API is not
running, the page now says so explicitly instead of spinning forever.

To point it at a hosted API instead, rebuild and redeploy:

```bash
pwsh ./scripts/deploy-pages.ps1 -ApiBaseUrl https://your-api.example.com
```

## Architecture

```text
.
├── back-end/                 # Express + TypeScript + Prisma REST API (port 5000)
│   ├── prisma/
│   │   ├── migrations/       # SQL migrations
│   │   ├── schema.prisma     # single Recommendation model
│   │   └── seed.ts           # idempotent demo data
│   ├── src/
│   │   ├── app.ts            # express app, CORS, routers, error handler
│   │   ├── server.ts         # entry point
│   │   ├── controllers/  routers/  services/  repositories/
│   │   ├── schemas/          # joi validation
│   │   └── middlewares/  utils/
│   └── tests/                # jest: 14 unit + 12 integration
├── front-end/                # Create React App SPA (port 3000)
│   ├── src/
│   │   ├── pages/Timeline/   # Home, Top, Random
│   │   ├── components/       # Header, Menu, Recommendation, ...
│   │   ├── hooks/            # useAsync + one hook per endpoint
│   │   └── services/         # axios instance + endpoint wrappers
│   └── cypress/e2e/          # 11 end-to-end tests
├── docker-compose.yml        # local PostgreSQL (dev + test databases)
├── render.yaml               # API deploy blueprint
└── scripts/                  # Pages deploy + test-db bootstrap
```

**Request flow:** `router → controller (validates) → service (business rules)
→ repository (Prisma) → PostgreSQL`. Errors are thrown as tagged objects and
mapped to status codes by `errorHandlerMiddleware`.

### API

| Method | Route | Behaviour |
| --- | --- | --- |
| `GET` | `/health` | `{ "status": "ok" }` |
| `POST` | `/recommendations` | Create. `201`; `422` invalid body; `409` duplicate name |
| `GET` | `/recommendations` | 10 most recent, newest first |
| `GET` | `/recommendations/random` | Random pick, 70% biased to score > 10; `404` when empty |
| `GET` | `/recommendations/top/:amount` | Top N by score, descending |
| `GET` | `/recommendations/:id` | One recommendation; `404` unknown; `422` non-numeric id |
| `POST` | `/recommendations/:id/upvote` | Score +1 |
| `POST` | `/recommendations/:id/downvote` | Score -1; deletes the row below -5 |
| `DELETE` | `/tests/reset` | **Only mounted when `MODE=TEST`.** Truncates the table |

`youtubeLink` must match `^(https?://)?(www\.youtube\.com|youtu\.?be)/.+$`.

## Requirements

- **Node.js 18+** (developed and verified on 20.18)
- **PostgreSQL 14+** (verified on 16) — or `docker compose up -d`

## Environment variables

Nothing secret is committed. Copy the templates and fill in your own values;
`.env*` is git-ignored apart from the `*.example` files.

### `back-end/.env` — from [`back-end/.env.example`](back-end/.env.example)

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | yes | Postgres connection string used by Prisma |
| `PORT` | no | API port, defaults to `5000` |
| `NODE_ENV` | no | `development` \| `test` \| `production` |
| `MODE` | no | `TEST` mounts `DELETE /tests/reset`. **Never set in production** |

### `back-end/.env.test` — from [`back-end/.env.test.example`](back-end/.env.test.example)

Same keys, but `DATABASE_URL` **must** point at a throw-away database: the
suites `TRUNCATE` and `migrate reset` it. `MODE=TEST` is required here.

### `front-end/.env` — from [`front-end/.env.example`](front-end/.env.example)

| Variable | Required | Purpose |
| --- | --- | --- |
| `REACT_APP_API_BASE_URL` | no | API base URL, no trailing slash. Defaults to `http://localhost:5000` |

CRA inlines `REACT_APP_*` at **build** time — rebuild after changing it, and
never put a secret in it, because it ships to the browser.

## Running locally

**1. Database.** Either use an existing PostgreSQL, or:

```bash
docker compose up -d
```

That creates `singmeasong` and `singmeasong_test` with the throw-away
credentials `singmeasong:singmeasong`.

**2. Back-end.**

```bash
cd back-end
cp .env.example .env
cp .env.test.example .env.test
npm install
npx prisma migrate deploy
npm run prisma:seed
npm run dev
```

The API listens on <http://localhost:5000>; check `GET /health`.

**3. Front-end**, in a second terminal:

```bash
cd front-end
cp .env.example .env
npm install
npm start
```

Open <http://localhost:3000>.

### Scripts

| Where | Command | What it does |
| --- | --- | --- |
| back-end | `npm run dev` | nodemon + ts-node ESM loader, watches `src/` |
| back-end | `npm run build` | `prisma generate` then `tsc` into `dist/` |
| back-end | `npm start` | Runs the compiled `dist/server.js` |
| back-end | `npm run prisma:deploy` | Applies migrations |
| back-end | `npm run prisma:seed` | Inserts three demo recommendations |
| back-end | `npm test` | Resets the test DB, runs all 26 jest tests |
| back-end | `npm run test:unit` / `test:integration` | One suite only |
| front-end | `npm start` / `npm run build` | CRA dev server / production bundle |
| front-end | `npm run cy:run` / `cy:open` | Cypress headless / interactive |

### Running the tests

Back-end (needs the **test** database only):

```bash
cd back-end
npm test
```

End-to-end (needs the API in test mode, the dev server, and the test database):

```bash
# terminal 1 - API against the test database, with the reset route mounted
cd back-end && npm run build && npx dotenv -e .env.test -- node dist/server.js

# terminal 2
cd front-end && npm start

# terminal 3
cd front-end && npm run cy:run
```

Override the targets with `CYPRESS_BASE_URL` and `CYPRESS_API_BASE_URL`.

## Deploying

### API — Render blueprint

[`render.yaml`](render.yaml) provisions a free Postgres instance and a web
service, and injects `DATABASE_URL` from the database, so no connection string
is stored in the repository.

1. Render dashboard → **New → Blueprint**, point it at this repo and the
   `723-oeh-singmeasong` branch.
2. Build runs `npm ci && npm run build && npx prisma migrate deploy`;
   start runs `npm start`. Health check is `/health`.
3. Leave `MODE` unset so `DELETE /tests/reset` stays off.

Any Node host works the same way: set `DATABASE_URL`, run
`npm ci && npm run build && npx prisma migrate deploy`, then `npm start`.

### Front-end — GitHub Pages

```bash
pwsh ./scripts/deploy-pages.ps1 -ApiBaseUrl https://your-api.example.com
```

The script builds with the correct `PUBLIC_URL`, copies `index.html` to
`404.html` (GitHub Pages has no SPA rewrite, so a hard reload of `/top` would
otherwise 404) and pushes to the `gh-pages` branch.

> `ai-training-workspace-may` is private and the account plan does not allow
> GitHub Pages on private repositories, so the published bundle lives in the
> dedicated public repo
> [`sing-me-a-song-deploy`](https://github.com/ManuDiasCruz/sing-me-a-song-deploy).
> Only the compiled front-end is there; the source stays private.

### Continuous integration

[`.github/workflows/sing-me-a-song-ci.yml`](.github/workflows/sing-me-a-song-ci.yml)
runs the jest suites against a Postgres service container and builds the
front-end with `CI=true` on every push to the branch.

## What was fixed

Nothing in the imported project ran: the API crashed on boot, the front-end
never reached the API, and none of the four test suites executed.

### Back-end

| Problem | Fix |
| --- | --- |
| `testController.ts` / `testService.ts` imported without the `.js` suffix. Under `"type": "module"` Node threw `ERR_MODULE_NOT_FOUND`, and since `app.ts` imports the test router unconditionally, **the server crashed on every boot** | Added the extensions |
| ts-node 10.7's ESM loader is rejected by Node ≥ 20 (`ERR_LOADER_CHAIN_INCOMPLETE`) | Bumped to 10.9.2 |
| `nodemon src/server.ts` invoked bare ts-node, which cannot load ESM | Added `nodemon.json` with an ESM `execMap` |
| `tsconfig.json` had no `target` (defaulted to ES3), no `rootDir`, no `include`; `tsc` emitted nothing usable | Set ES2020 / `rootDir: src` / `outDir: dist` |
| No `build` script, and `start` pointed at `dist/index.js`, which is never produced | Added `build`; `start` now runs `dist/server.js` |
| `PORT` and `MODE` were read from `process.env`, but nothing loaded `.env` | `import "dotenv/config"` in `server.ts` |
| `prisma.seed` pointed at `prisma/seed.ts`, which did not exist | Added an idempotent seeder |
| `/recommendations/abc` and `/top/abc` coerced to `NaN`, so Prisma threw and the API answered **500** | Params validated; **422** with a message |
| `react-player` (a React component library) was a runtime dependency of the API | Removed |
| No back-end env template at all | `.env.example` + `.env.test.example` |

### Front-end

| Problem | Fix |
| --- | --- |
| `.env.example` contained the truncated `REACT_APP_API_BASE_URL=http://`, and no `.env` existed, so axios built relative URLs, every call 404'd against the dev server and the page never left "Loading..." | Real template plus a `http://localhost:5000` fallback in `api.js` |
| `App.js` imported `Component` and never used it; `react-scripts` turns warnings into errors when `CI=true`, so **every CI build failed** | Removed the import |
| A failed request left the UI on "Loading..." with no explanation | Hooks expose the error; pages render a `LoadError` panel naming the failing URL |
| `BrowserRouter` had no `basename`, so the app could not be served from a sub-path | `basename={process.env.PUBLIC_URL}` |
| The Cypress selectors `vote-menu` / `upvote` / `downvote` were never rendered | Added the `data-identifier` attributes |
| Document title was "React App" | "Sing me a Song" |

### Tests

| Problem | Fix |
| --- | --- |
| `jest.config.js` used the CommonJS `ts-jest` preset in an ESM package: `ReferenceError: exports is not defined`, and `import pkg from "@prisma/client"` resolved to `undefined` | Switched to `ts-jest/presets/default-esm` |
| Test scripts used an inline `NODE_OPTIONS=...` prefix, which is not valid shell on Windows | Routed through `cross-env` |
| `dotenv -e .env.test jest -- -i ./tests/unit` handed the flags to dotenv-cli, not jest | Added the `--` separators |
| `prisma migrate reset` prompted for confirmation and hung | `--force` |
| `recommendationFactory` called `require()` inside an ES module, for a package (`random-youtube-music-video`) that was never in `package.json` | Faker-built URL matching the joi pattern, plus a counter for the `UNIQUE` name |
| `scenariosFactory` declared four helpers and exported none | Exported |
| "List recommendations" expected the order `2, 1, 3` — neither ascending nor descending | Newest-first, matching `orderBy: { id: "desc" }` |
| "List top recommendations" read an id from a `201` response with no body, upvoted `/recommendations/undefined/upvote`, then relied on an arbitrary tie-break | Reads the ids back, gives the winners distinct scores |
| Three of four Cypress specs were named `.tests.js`, which the default `specPattern` ignores | Renamed to `.cy.js` |
| They imported a non-existent `./utils/setup.js` and called unregistered commands | Added the helper and the commands |
| `cy.resetData` hit `/reset`; the route is `/tests/reset` | Corrected |
| `cypress/e2e/2-advanced-examples` (Cypress scaffolding) drives `example.cypress.io` and fails offline | Removed |
| "Show only 10 posts" seeded itself with invalid links, so every POST was rejected and the list stayed empty | Seeds valid recommendations |
| `vote.post` shared one row across all four tests, asserted on scores left by the previous one, hard-coded id `1`, and referenced an undefined `musicData` | Each test seeds its own row |

Result: **26 jest tests and 11 Cypress tests pass.**

## Known limitations and next steps

- **The API is not publicly hosted.** No hosting credentials were available in
  this environment, so only the blueprint ships. The deployed front-end talks
  to `http://localhost:5000`.
- **Dependencies are from 2022** and `npm audit` reports vulnerabilities in
  both workspaces (Prisma 3.13, CRA 5, `@faker-js/faker` 7). Upgrading is a
  separate, breaking change; it was left out to keep this branch reviewable.
- **`POST /recommendations` returns `201` with an empty body.** Clients cannot
  learn the new id without re-querying, which both the integration and the
  Cypress suites have to work around.
- **The front-end refetches the whole list after every vote**, so a busy
  timeline flickers and does N+1 requests.
- **No pagination.** `GET /recommendations` is hard-coded to `take: 10`.
- **No rate limiting or auth**, so anyone can vote without limit.
- **`docs/parrot-memory-card-game.md`** is unrelated to this project; it is the
  previous root README, kept so nothing is lost.

Each of these is filed as a GitHub issue against `723-oeh-singmeasong`.
