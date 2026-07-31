# 🎵 Sing me a Song

Anonymous song recommendations: anyone can post a YouTube link with a name,
vote recommendations up or down, browse the highest-scored ones, or ask for a
random suggestion.

This branch (`723-feh-singmeasong`) imports the original
[`ManuDiasCruz/sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song)
project and repairs it so it installs, runs, passes its test suite, builds and
deploys. The repository also hosts an unrelated static
[Parrot Memory Card Game](docs/parrot-memory-card-game.md) (`index.html`,
`css/`, `src/`, `img/`), whose original documentation is preserved in
[`docs/parrot-memory-card-game.md`](docs/parrot-memory-card-game.md).

## Stack

| Layer     | Tech                                                                  |
| --------- | --------------------------------------------------------------------- |
| back-end  | Node.js 20, Express 4, TypeScript (ESM), Prisma 3, PostgreSQL         |
| front-end | React 18 (Create React App 5), styled-components, axios, react-player |
| tests     | Jest + supertest (back-end unit & integration), Cypress (front-end E2E) |

```text
.
├── back-end/    Express + Prisma REST API
├── front-end/   React SPA
├── scripts/     deploy-server.mjs (single-origin static + API proxy)
├── docs/        preserved docs for the other project in this repo
└── render.yaml  Render blueprint for permanent hosting
```

## API

| Method | Route                          | Description                                    |
| ------ | ------------------------------ | ---------------------------------------------- |
| GET    | `/health`                      | health probe, returns `OK`                     |
| GET    | `/recommendations`             | last 10 recommendations (newest first)         |
| GET    | `/recommendations/random`      | one random recommendation (score-weighted)     |
| GET    | `/recommendations/top/:amount` | top `:amount` by score                         |
| GET    | `/recommendations/:id`         | one recommendation by id                       |
| POST   | `/recommendations`             | create `{ name, youtubeLink }` (YouTube links only) |
| POST   | `/recommendations/:id/upvote`  | score +1                                       |
| POST   | `/recommendations/:id/downvote`| score −1 (removed when score drops below −5)   |

## Running locally

### Prerequisites

- Node.js 18+ (verified on Node 20)
- A running PostgreSQL server (verified on PostgreSQL 16)

### 1. Database

Create two databases — one for development, one that the test suite may wipe:

```bash
psql -U postgres -c "CREATE DATABASE singmeasong;"
psql -U postgres -c "CREATE DATABASE singmeasong_test;"
```

### 2. Back-end

```bash
cd back-end
npm install
cp .env.example .env            # then edit DATABASE_URL if needed
cp .env.test.example .env.test  # test-only database
npx prisma migrate deploy       # applies prisma/migrations
npx prisma generate
npm run dev                     # http://localhost:5000
```

Required environment variables (`back-end/.env`, see
[`.env.example`](back-end/.env.example)):

| Variable       | Required | Example                                                  | Notes                                        |
| -------------- | -------- | -------------------------------------------------------- | -------------------------------------------- |
| `DATABASE_URL` | yes      | `postgresql://postgres:postgres@localhost:5432/singmeasong` | Prisma connection string                     |
| `PORT`         | no       | `5000`                                                    | defaults to `5000`                           |
| `MODE`         | no       | `TEST`                                                    | `TEST` mounts `DELETE /tests/reset` (E2E only) |

`back-end/.env.test` (see [`.env.test.example`](back-end/.env.test.example))
must point at the **test** database — `npm test` runs
`prisma migrate reset` against it on every run.

### 3. Front-end

```bash
cd front-end
npm install
cp .env.example .env   # REACT_APP_API_BASE_URL=http://localhost:5000
npm start              # http://localhost:3000
```

| Variable                 | Required   | Example                 | Notes                                                        |
| ------------------------ | ---------- | ----------------------- | ------------------------------------------------------------ |
| `REACT_APP_API_BASE_URL` | at build   | `http://localhost:5000` | baked into the bundle at build time; leave **empty** for same-origin deployments |

## Tests

```bash
cd back-end
npm test                  # migrate-reset test DB + full Jest suite (26 tests)
npm run test:unit         # unit tests only
npm run test:integration  # integration tests only (needs .env.test)
```

Front-end E2E (Cypress) expects the back-end running in TEST mode
(`npm run dev:test`) and the front-end on port 3000:

```bash
cd front-end
npx cypress open   # or: npx cypress run
```

## Deployment

### Verified demo deployment (no accounts required)

The production artifacts were deployed behind a single public HTTPS origin and
verified end to end (page load, listing, creating, voting, SPA routes,
health probe):

```bash
# 1. build + start the API
cd back-end && npm ci && npm run build && npx prisma migrate deploy && npm start

# 2. build the front-end for same-origin serving (empty API base URL)
cd front-end && npm ci && REACT_APP_API_BASE_URL= npm run build

# 3. serve SPA + proxy API on one origin (http://localhost:8080)
node scripts/deploy-server.mjs

# 4. expose it publicly via a keyless SSH tunnel
ssh -R 80:localhost:8080 nokey@localhost.run   # prints the public https URL
```

[`scripts/deploy-server.mjs`](scripts/deploy-server.mjs) (Node stdlib only)
serves `front-end/build` with an SPA fallback and reverse-proxies
`/recommendations`, `/tests` and `/health` to the API — one origin, so no CORS
and no absolute API URL baked into the bundle, and the public URL can change
without a rebuild. Tunnel URLs from localhost.run are ephemeral; use the
blueprint below for permanent hosting.

### Permanent hosting (Render blueprint)

[`render.yaml`](render.yaml) provisions a free PostgreSQL database, the API
(with `prisma migrate deploy` on boot and `/health` as health check) and the
static front-end with SPA rewrites:

1. Render dashboard → **New** → **Blueprint** → pick this repository/branch.
2. After the first deploy, set `REACT_APP_API_BASE_URL` on `singmeasong-web`
   to the `singmeasong-api` URL and trigger a rebuild (the value is baked in
   at build time).

## Fixes and improvements made on this branch

Everything below was broken in the imported project and is repaired here with
the smallest safe change (no architectural rewrites):

1. **Dev server crashed on Node 20** — `nodemon src/server.ts` invoked plain
   `ts-node`, which cannot load `.ts` under ESM (`ERR_UNKNOWN_FILE_EXTENSION`),
   and ts-node 10.7 was incompatible with Node 20's loader chain
   (`ERR_LOADER_CHAIN_INCOMPLETE`). `dev`/`dev:test` now run nodemon with
   `node --loader ts-node/esm`; ts-node bumped to 10.9.2.
2. **Server crashed on boot in TEST mode** — `testController.ts` and
   `testService.ts` imported relative modules without the `.js` extension
   required by Node ESM.
3. **Production start never worked** — `npm start` pointed at
   `dist/index.js`, which no build produced. Added `npm run build` (tsc,
   compiling only `src/` to `dist/`) and pointed `start` at `dist/server.js`.
4. **Test scripts were POSIX-only** — inline `NODE_OPTIONS=...` failed on
   Windows; now uses `cross-env` (already a dependency).
5. **`npm test` hung in non-interactive shells** — `prisma migrate reset`
   needed `--force`, and dotenv-cli was swallowing the flag; pass it through
   with the `--` separator.
6. **Test suite failed 8 of 12 tests** — the factory `require()`d
   `random-youtube-music-video`, a package missing from `package.json` and
   unavailable under ESM; it now generates faker-based YouTube URLs
   (deterministic, offline). One assertion expected order `(2,1,3)` from an
   endpoint that returns newest-first; corrected to `(3,2,1)`.
   **Result: 26/26 passing.**
7. **Environment undocumented** — back-end had no `.env.example` at all and
   front-end's was truncated (`REACT_APP_API_BASE_URL=http://`); both added /
   completed, with `.env*` still gitignored so no secrets are committed.
8. **No deployment story** — added `/health` endpoint, single-origin deploy
   server, Render blueprint, and this README.

## Known limitations / future improvements

- **Prisma 3.13 is EOL** — upgrade to Prisma 5+ for Node 22+ support and
  maintained security fixes.
- **`react-player` is an unused back-end dependency** (front-end package in
  an Express API) and should be removed.
- **CORS is wide open** (`app.use(cors())`); restrict `origin` to the
  deployed front-end URL in production.
- **No CI** — a GitHub Actions workflow running build + tests on PRs would
  prevent regressions like the ones fixed here.
- **Score can be voted on stale UI state** — votes always succeed; the list
  refetches after each vote, but concurrent voters can briefly see stale
  scores (acceptable for this app's scope).
- **Cypress specs include CRA example tests** — the generated
  `1-getting-started`/`2-advanced-examples` folders should be pruned and the
  project's own specs wired into CI.
- **localhost.run demo URLs are ephemeral** — the tunnel deployment is for
  verification/demo; use the Render blueprint (or any Node + Postgres host)
  for something permanent.
