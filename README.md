# Sing Me a Song

Sing Me a Song is a full-stack music recommendation application. People submit
YouTube videos, browse the ten newest recommendations, discover a weighted
random recommendation, view the highest-scoring songs, and upvote or downvote
each entry. Recommendations are removed automatically once their score drops
below `-5`.

This branch preserves the original React frontend and Express/TypeScript/Prisma
backend from [the original Sing Me a Song repository](https://github.com/ManuDiasCruz/sing-me-a-song).
The original Create React App instructions are still available in
[`front-end/README.md`](front-end/README.md).

## Project structure

```text
back-end/              Express API, Prisma schema/migrations, Jest tests
front-end/             React application, component tests, Cypress tests
site/worker.js         Production Sites adapter with the same recommendation API
db/schema.ts           Documented hosted recommendation schema
drizzle/               Hosted durable-database migration
scripts/               Sites build and end-to-end smoke-test helpers
docker-compose.yml     Local PostgreSQL database
render.yaml            Optional single-service Render/PostgreSQL blueprint
.github/workflows/     PostgreSQL-backed continuous integration
```

The normal development architecture is React + Express + Prisma + PostgreSQL.
The Sites deployment serves the same React build and preserves the API contract
through a small worker adapter backed by durable D1 storage. The optional Render
blueprint runs the original Express/Prisma/PostgreSQL implementation directly.

## Requirements

- Node.js 18 or newer; Node.js 20 LTS is recommended.
- npm, included with a normal Node.js installation.
- PostgreSQL 14 or newer, or Docker Compose for the included local database.
- Internet access for dependency installation and embedded YouTube playback.

## Local setup

1. Install both dependency trees from the repository root:

   ```bash
   npm run install:all
   ```

2. Start PostgreSQL using the supplied development container:

   ```bash
   docker compose up -d postgres
   ```

   Alternatively, use any PostgreSQL instance and update the connection URLs in
   the next step.

3. Create local environment files from the safe examples:

   ```bash
   cp back-end/.env.example back-end/.env
   cp back-end/.env.test.example back-end/.env.test
   cp front-end/.env.example front-end/.env
   ```

   On Windows PowerShell, use `Copy-Item` instead of `cp` if needed.

4. Apply the application database migration:

   ```bash
   npm --prefix back-end run db:migrate
   ```

5. Start each application in its own terminal:

   ```bash
   npm run dev:backend
   npm run dev:frontend
   ```

   Open `http://localhost:3000`; the API listens on `http://localhost:5000`.
   `GET http://localhost:5000/health` also verifies database connectivity.

### Environment variables

Backend values are documented in `back-end/.env.example`:

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | `postgresql://postgres:postgres@localhost:5432/sing_me_a_song?schema=public` | Prisma PostgreSQL connection string. |
| `PORT` | No | `5000` | Express HTTP port. |
| `MODE` | No | `DEVELOPMENT` | Set to `TEST` only when test-reset endpoints are required. |
| `CORS_ORIGIN` | No | `http://localhost:3000` | Allowed frontend origin; comma-separated origins are supported. |

Frontend values are documented in `front-end/.env.example`:

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `REACT_APP_API_BASE_URL` | Local split-server development | `http://localhost:5000` | API origin; omit it for same-origin production deployments. |

Use `back-end/.env.test.example` for a separate test database. Real `.env` and
`.env.test` files, dependencies, build artifacts, and local database data are
excluded from Git. Never commit production connection strings or credentials.

## API routes

| Method and route | Behavior |
| --- | --- |
| `GET /health` | Confirms the server can reach its database. |
| `GET /recommendations` | Lists the ten newest recommendations. |
| `POST /recommendations` | Creates a validated recommendation and returns it. |
| `GET /recommendations/random` | Returns a weighted random recommendation. |
| `GET /recommendations/top/:amount` | Lists the highest-scoring recommendations. |
| `GET /recommendations/:id` | Retrieves one recommendation. |
| `POST /recommendations/:id/upvote` | Increases the recommendation score. |
| `POST /recommendations/:id/downvote` | Decreases the score and deletes entries below `-5`. |
| `DELETE /tests/reset` | Clears test data; available only when `MODE=TEST`. |

Invalid payloads and route parameters return `422`, duplicate names return
`409`, and missing recommendations return `404`.

## Running tests

Create the separate test database before running integration tests:

```bash
docker compose exec postgres psql -U postgres -c "CREATE DATABASE sing_me_a_song_test;"
```

Then run the complete backend suite, including migrations:

```bash
npm test
```

Focused checks are also available:

```bash
npm run test:unit
npm run test:integration
npm run test:frontend
npm run test:site
npm run build
```

To run Cypress, start the frontend plus the backend in its isolated test mode:

```bash
npm --prefix back-end run dev:test
npm --prefix front-end start
npx --prefix front-end cypress run
```

The reusable smoke test exercises health checks, creation, uniqueness conflicts,
listing, voting, top/random routes, removal below `-5`, and SPA routes:

```bash
BASE_URL=http://localhost:5000 npm run test:smoke
```

For PowerShell, set `$env:BASE_URL='http://localhost:5000'` first.

## Deployment

### Sites deployment

The committed `.openai/hosting.json` requests a durable `DB` database. Build the
existing React application and its compatible production API adapter with:

```bash
npm run build:site
```

The build outputs the deployable worker, frontend assets, hosting metadata, and
database migration under `dist/`. Publish that exact build using the Sites
hosting integration. No PostgreSQL credentials or production secrets are stored
in the repository; the hosting provider provisions and binds the database.

After deployment, verify `/health`, `/`, `/top`, `/random`, and the recommendation
API. The hosted deployment is private to its owner unless its access policy is
explicitly changed.

### Render / PostgreSQL deployment

Import this repository into Render and choose the included `render.yaml`
blueprint. It provisions a PostgreSQL database, injects `DATABASE_URL`, installs
both application dependency trees, builds the frontend/backend, applies Prisma
migrations, and starts the original Express application. Express serves the
production React build and handles client-side route fallbacks on the same
origin.

For another Node.js host, use equivalent commands:

```bash
npm run install:all
npm run build
npm --prefix back-end run db:migrate
npm start
```

Configure `DATABASE_URL` and allow the host to provide `PORT`. Leave
`REACT_APP_API_BASE_URL` unset for same-origin frontend/API requests.

## Repairs and improvements

- Fixed the backend production entry point and added a real TypeScript build.
- Repaired ESM imports, environment loading, database migrations, CORS settings,
  and PostgreSQL-backed health checks.
- Returned created recommendation records from the API, validated numeric route
  parameters, handled uniqueness failures safely, and made ranking deterministic.
- Replaced a missing, undeclared test dependency with self-contained fixtures;
  repaired incorrect integration assertions and asynchronous unit assertions.
- Added regression coverage for invalid identifiers, health checks, returned
  records, and automatic removal below `-5`.
- Repaired frontend API defaults, loading/error states, vote controls, accessible
  labels, application metadata, and empty random-recommendation handling.
- Corrected Cypress test routing and restricted discovery to the maintained
  recommendation suite.
- Added root setup scripts, safe environment examples, Docker Compose, CI,
  production hosting support, a Render blueprint, and end-to-end smoke testing.

## Known limitations and future improvements

- Recommendations and voting remain anonymous; authentication, abuse prevention,
  moderation, and request throttling are future improvements.
- The original Create React App, Prisma 3, and Jest/ESM stack is preserved to
  avoid an architectural rewrite; a carefully tested dependency modernization
  would improve long-term maintainability.
- YouTube embeds require third-party network access and may be blocked by some
  browsers, privacy extensions, or the video's owner.
- Browser end-to-end coverage currently requires a locally running frontend and
  a dedicated test-mode backend.
- Sites uses durable D1 storage while the original local/Render backend uses
  PostgreSQL; both expose the same recommendation API, but their infrastructure
  is intentionally different.
