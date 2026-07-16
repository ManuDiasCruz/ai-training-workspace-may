# Sing me a Song

Full-stack app for anonymous song recommendations: post a song with its
YouTube link, watch it inline, and upvote/downvote what others recommended.
Recommendations that drop below a score of -5 are removed automatically.

- **back-end/** — Node.js + Express + TypeScript (ESM), Prisma ORM, PostgreSQL
- **front-end/** — React 18 (Create React App), styled-components, axios

> This branch (`fb-ehe-sing-me-a-song`) imports the original
> [sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song) project and
> repairs it so it runs, tests green and deploys. See
> [Fixes made on this branch](#fixes-made-on-this-branch).

## Project structure

```
.
├── back-end/
│   ├── prisma/              # schema + migrations (PostgreSQL)
│   ├── src/
│   │   ├── routers/         # /recommendations, /tests (test mode only)
│   │   ├── controllers/ → services/ → repositories/  # layered API
│   │   └── server.ts        # entry point (loads .env, starts Express)
│   └── tests/               # jest + supertest (unit + integration)
└── front-end/
    ├── src/                 # pages (Home, Top, Random), hooks, services
    └── cypress/             # e2e specs
```

### API reference

| Method | Route                          | Description                              |
| ------ | ------------------------------ | ---------------------------------------- |
| POST   | `/recommendations`             | Create recommendation `{name, youtubeLink}` (YouTube URLs only) |
| GET    | `/recommendations`             | Last 10 recommendations                  |
| GET    | `/recommendations/random`      | One random recommendation (70% chance score > 10) |
| GET    | `/recommendations/top/:amount` | Top `:amount` by score                   |
| GET    | `/recommendations/:id`         | One recommendation by id                 |
| POST   | `/recommendations/:id/upvote`  | +1 score                                 |
| POST   | `/recommendations/:id/downvote`| −1 score (removed when score < −5)       |
| DELETE | `/tests/reset`                 | Truncate table — only when `MODE=TEST`   |

## Requirements

- Node.js 18+ (developed/verified on Node 20)
- PostgreSQL 12+ running locally (or a connection string to a hosted one)

## Running locally

### 1. Back-end

```bash
cd back-end
npm install

# configure environment
cp .env.example .env          # then edit DATABASE_URL if needed

# create the database and apply migrations
createdb singmeasong          # or: CREATE DATABASE singmeasong; via psql
npx prisma migrate deploy
npx prisma generate

# development (watch mode)
npm run dev                   # http://localhost:5000

# production
npm run build && npm start
```

### 2. Front-end

```bash
cd front-end
npm install
cp .env.example .env          # REACT_APP_API_BASE_URL=http://localhost:5000
npm start                     # http://localhost:3000
```

### Required environment variables

| App       | Variable                 | Example                                                | Notes                        |
| --------- | ------------------------ | ------------------------------------------------------ | ---------------------------- |
| back-end  | `DATABASE_URL`           | `postgresql://postgres:postgres@localhost:5432/singmeasong` | Prisma connection string |
| back-end  | `PORT`                   | `5000`                                                 | optional, defaults to 5000   |
| back-end  | `MODE`                   | `TEST`                                                 | only for test runs — enables `DELETE /tests/reset` |
| front-end | `REACT_APP_API_BASE_URL` | `http://localhost:5000`                                | baked in at build time (CRA) |

Copy `.env.example` → `.env` (and `.env.test.example` → `.env.test` for the
back-end test suite). Real `.env` files are git-ignored; never commit
credentials.

## Tests

```bash
cd back-end
cp .env.test.example .env.test   # points at a separate singmeasong_test DB
createdb singmeasong_test
npm test                         # resets the test DB, runs unit + integration
```

26 tests in 2 suites (unit + integration) — all passing on this branch.

Front-end e2e specs live in `front-end/cypress/` and expect the back-end
running in test mode (`npm run dev:test`) so they can reset state via
`DELETE /tests/reset`.

## Deployment

The app is deployed on [Render](https://render.com) (free tier):

- **API** — Render *Web Service*, root dir `back-end`,
  build `npm ci && npm run build`,
  start `npx prisma migrate deploy && npm start`,
  env: `DATABASE_URL` (from a Render PostgreSQL instance).
- **Front-end** — Render *Static Site*, root dir `front-end`,
  build `npm ci && npm run build`, publish dir `build`,
  env: `REACT_APP_API_BASE_URL` = the API's public URL (CRA bakes it in at
  build time — changing it requires a rebuild).
- **Database** — Render PostgreSQL (free), connected via `DATABASE_URL`.

CORS is open on the API (`app.use(cors())`), so the static front-end can call
it cross-origin without extra configuration.

Any equivalent stack works the same way (Railway, Fly.io, a VPS): host
PostgreSQL, run `npm run build && npx prisma migrate deploy && npm start` for
the API, and serve the CRA `build/` folder statically with
`REACT_APP_API_BASE_URL` pointing at the API.

## Fixes made on this branch

Runtime / configuration:

1. **`.env` never loaded** — `server.ts` did not import `dotenv/config`, so
   `DATABASE_URL` was unavailable and the first query crashed the server.
2. **Invalid ESM imports** — `testController.ts` and `testService.ts` used
   extensionless relative imports, which crash on startup in an ESM
   (`"type": "module"`) project. Added the required `.js` extensions.
3. **Broken npm scripts** — `dev` invoked plain `ts-node` (fails with
   `ERR_UNKNOWN_FILE_EXTENSION` under ESM); there was no `build` script; and
   `start` pointed at a nonexistent `dist/index.js`. Now: `dev` runs nodemon
   through `node --loader ts-node/esm`, `build` runs `tsc`, `start` runs the
   real compiled entry `dist/server.js`.
4. **ts-node incompatible with Node 20** — bumped `ts-node` 10.7 → 10.9
   (`ERR_LOADER_CHAIN_INCOMPLETE` on modern Node).
5. **tsconfig** — set an explicit `ES2020` target and compile only `src/`
   so tests are not emitted into `dist/`.
6. **Windows-portable test scripts** — `NODE_OPTIONS=...` env prefix now goes
   through `cross-env`; `prisma migrate reset` gets `--force` so it runs
   non-interactively.

Tests:

7. **Broken test factory** — used CommonJS `require()` (invalid in ESM) on
   `random-youtube-music-video`, a package that was never in `package.json`
   and needed network access. Replaced with a faker-generated YouTube URL.
8. **Wrong assertions** — the list test asserted an order that contradicts
   the API's `id desc` ordering; the top-recommendations test read `body.id`
   from a `sendStatus(201)` response that has no JSON body.

Documentation / setup:

9. **Env documentation** — added `back-end/.env.example`,
   `back-end/.env.test.example` and fixed the invalid
   `front-end/.env.example` placeholder (`http://`).

## Known limitations / future improvements

- **Prisma 3 is EOL** — upgrading to Prisma 5+ needs a coordinated
  client/schema migration.
- **No YouTube URL content validation** — any URL matching the regex is
  accepted even if the video doesn't exist.
- **Random page throws for empty DB** — `/recommendations/random` returns 404
  when there are no recommendations; the front-end shows a permanent loading state
  instead of an empty-state message.
- **Cypress e2e specs are stale** — they were written for an older UI and are
  not wired into CI.
- **No CI pipeline** — tests only run locally.
- **CRA is deprecated** — a future migration to Vite would speed up builds.

The stock Create React App documentation is preserved in
[front-end/README.md](front-end/README.md).
