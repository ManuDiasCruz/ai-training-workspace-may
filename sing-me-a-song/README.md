# Sing me a Song

Sing me a Song is an anonymous song-recommendation app. Anyone can post a
recommendation (a name plus a YouTube link), upvote or downvote existing
recommendations, browse the newest ones, see the top-scored ones, or get a
random suggestion. A recommendation whose score drops below **-5** is removed
automatically.

Front-end deployment: the production build is published on the `gh-pages`
branch under `0827-faeh-singasong/`. Once GitHub Pages is enabled for this
repository (one manual step, see [Deployment](#deployment)) it is served at
**https://manudiascruz.github.io/ai-training-workspace-may/0827-faeh-singasong/**.

## Project structure

```
sing-me-a-song/
├── back-end/    Node.js + Express + TypeScript + Prisma (PostgreSQL)
├── front-end/   React 18 (Create React App) + styled-components
└── deploy/      Deployment helper scripts
```

### API routes

| Method | Route                          | Description                              |
| ------ | ------------------------------ | ---------------------------------------- |
| POST   | `/recommendations`             | Create a recommendation (`name`, `youtubeLink`) |
| GET    | `/recommendations`             | List the 10 newest recommendations       |
| GET    | `/recommendations/random`      | Get a random recommendation              |
| GET    | `/recommendations/top/:amount` | Top `:amount` recommendations by score   |
| GET    | `/recommendations/:id`         | Get one recommendation                   |
| POST   | `/recommendations/:id/upvote`  | +1 score                                 |
| POST   | `/recommendations/:id/downvote`| -1 score (removed when score < -5)       |
| DELETE | `/tests/reset`                 | Truncate data — only exposed when `MODE=TEST` |

## Requirements

- Node.js 20+
- A running PostgreSQL instance

## Back-end setup

```bash
cd back-end
npm ci
cp .env.example .env        # then edit the values
npx prisma migrate deploy   # creates the recommendations table
npm run dev                 # development server (tsx watch)
```

Production build:

```bash
npm run build               # prisma generate + tsc -> dist/
npm start                   # node dist/server.js
```

### Back-end environment variables (`back-end/.env`)

| Variable       | Required | Description                                            |
| -------------- | -------- | ------------------------------------------------------ |
| `DATABASE_URL` | yes      | PostgreSQL connection string used by Prisma            |
| `PORT`         | no       | HTTP port (default `5000`)                             |
| `MODE`         | no       | Set to `TEST` to expose `DELETE /tests/reset` (never in production) |

See [`back-end/.env.example`](back-end/.env.example). **Never commit real
`.env` files** — they are git-ignored; only the `*.example` templates belong in git.

### Tests

```bash
cd back-end
cp .env.test.example .env.test   # point it at a DISPOSABLE test database
npm test                          # resets the test DB, runs unit + integration suites
npm run test:unit
npm run test:integration
```

## Front-end setup

```bash
cd front-end
npm ci
cp .env.example .env    # REACT_APP_API_BASE_URL=http://localhost:5000
npm start               # http://localhost:3000
```

### Front-end environment variables (`front-end/.env`)

| Variable                 | Required | Description                                  |
| ------------------------ | -------- | -------------------------------------------- |
| `REACT_APP_API_BASE_URL` | yes      | Base URL of the back-end API (no trailing slash) |

The deployed static build can also be pointed at any back-end **at runtime**
with a query parameter: `?api=https://my-backend.example.com` (persisted in
`localStorage` for subsequent visits).

### End-to-end tests (Cypress)

1. Start the back-end with `MODE=TEST` against a disposable database
   (`npm run dev:test` uses `.env.test`).
2. Start the front-end (`npm start`).
3. `cd front-end && npx cypress open` (or `npx cypress run`).

## Deployment

### Front-end — GitHub Pages

The production build is committed to the `gh-pages` branch in
`0827-faeh-singasong/` (following the pattern of earlier deployments on that
branch). **To make it live**, enable Pages once: repository **Settings →
Pages → Deploy from a branch → `gh-pages` / root** — or run:

```bash
gh api -X POST repos/ManuDiasCruz/ai-training-workspace-may/pages -f "source[branch]=gh-pages" -f "source[path]=/"
```

Note: this repository is currently **private**; GitHub Pages on private
repositories requires a paid GitHub plan. Making the repository public (or
mirroring the front-end build to a public repository) also works.

Once enabled it is served at
**https://manudiascruz.github.io/ai-training-workspace-may/0827-faeh-singasong/**.
The deployed bundle was verified end-to-end by serving the exact `gh-pages`
content at the same subpath locally against the production back-end build.

To redeploy:

```bash
cd front-end
PUBLIC_URL=/ai-training-workspace-may/0827-faeh-singasong \
REACT_APP_API_BASE_URL=http://localhost:5000 \
npm run build
# copy build/ into the 0827-faeh-singasong/ folder of the gh-pages branch and push
```

By default the hosted page calls `http://localhost:5000`, so it works
against a back-end you run locally (browsers allow `http://localhost`
requests from HTTPS pages). To pair it with a hosted back-end instead, open
it once with `?api=<backend-url>`.

### Back-end — options

The back-end needs Node plus PostgreSQL, so it requires an account on some
host (Render, Railway, Fly.io, a VPS…). Two ready-made paths:

- **GitHub Codespace** (needs a token with the `codespace` scope):

  ```bash
  gh codespace create -R ManuDiasCruz/ai-training-workspace-may -b 0827-faeh-singasong --idle-timeout 4h
  gh codespace ssh -c <codespace-name> -- bash /workspaces/ai-training-workspace-may/sing-me-a-song/deploy/codespace-deploy.sh
  gh codespace ports visibility 5000:public -c <codespace-name>
  # API: https://<codespace-name>-5000.app.github.dev
  ```

  [`deploy/codespace-deploy.sh`](deploy/codespace-deploy.sh) starts a
  dockerized PostgreSQL, applies migrations, builds and starts the server.

- **Render / Railway / similar**: create a PostgreSQL instance, set
  `DATABASE_URL` and `PORT` in the service environment, build with
  `npm ci && npm run build && npx prisma migrate deploy`, start with `npm start`.

## Fixes and improvements made (branch `0827-faeh-singasong`)

**Back-end — it did not start at all before these fixes:**

- Missing `.js` extensions in the ESM imports of `testController.ts` and
  `testService.ts` crashed module resolution on every boot.
- `dotenv.config()` was never called, so `PORT` and `MODE` from `.env` were
  silently ignored (only `DATABASE_URL` worked, because Prisma loads `.env`
  itself).
- The dev runtime (`ts-node` 10.7 via nodemon) fails on Node 18.19+/20 with
  `ERR_UNKNOWN_FILE_EXTENSION`; replaced with `tsx watch`.
- There was no `build` script, and `start` pointed at `dist/index.js` while
  the real compiled entry is `dist/server.js`. `tsc` also compiled the test
  files into `dist/`; it is now scoped to `src/` with an ES2020 target.

**Tests and tooling:**

- The test factory `require`d `random-youtube-music-video`, a package that is
  not a dependency (and `require` does not exist in ESM) — every suite failed
  to load. It now generates valid YouTube URLs with faker.
- `NODE_OPTIONS=... jest` in npm scripts does not work on Windows — wrapped
  with `cross-env`.
- `prisma migrate reset --force` never received `--force` because dotenv-cli
  swallowed it (missing `--` separator), so `npm test` hung in CI-like
  non-interactive shells.
- One integration test asserted an impossible ordering for
  `GET /recommendations`; it now asserts the actual (and correct)
  newest-first order.
- Cypress `resetData()` called `DELETE /reset`; the real route is
  `DELETE /tests/reset`. The "Add a song" spec referenced undefined
  variables and treated a sync factory as async.

**Configuration and deployment:**

- `front-end/.env.example` contained just `REACT_APP_API_BASE_URL=http://`;
  both apps now have complete, documented example env files.
- React Router now takes its `basename` from `PUBLIC_URL`, so the SPA works
  when hosted under a subpath (GitHub Pages).
- The API base URL of a static build can be overridden at runtime via
  `?api=<url>`.
- Removed `react-player` from back-end dependencies (front-end package) and
  committed `.DS_Store` artifacts.

## Known limitations / future improvements

- **GitHub Pages must be enabled once by the repository owner** (see
  Deployment); automation could not change repository settings, and Pages on
  a private repository needs a paid plan or a public repository.
- **Back-end hosting**: the GitHub Pages front-end defaults to a
  locally-run back-end; a durable public back-end (Render/Railway/Fly)
  requires account credentials and is documented above instead of deployed.
- Prisma 3 and CRA (react-scripts 5) are old; upgrading to Prisma 5+ and
  Vite would modernize the stack (left out to avoid rewrites).
- Deep links into the Pages deployment (e.g. `/top`) are handled by the
  repository's root 404 page, not this app — navigate from the app root.
- The `GET /recommendations/random` 70/30 score-based selection has no
  integration coverage for the fallback branch.
- No CI pipeline; the test suites are ready for one (see Next Steps issues).
