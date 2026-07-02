# Sing Me a Song

Sing Me a Song is a full-stack recommendation board for sharing YouTube songs. People can create recommendations, vote them up or down, browse the ten highest-scored songs, and request a weighted random selection. This branch preserves the original React/Express/Prisma architecture and applies targeted repairs so the project can build, run, and deploy predictably.

The source project's original Create React App documentation remains unchanged in [`front-end/README.md`](front-end/README.md).

## Project structure and request flow

```text
front-end/                 React 18 single-page application
  src/services/            Axios client and recommendation API requests
  src/hooks/               Shared asynchronous request state
  src/pages/Timeline/      Home, Top, and Random routes
back-end/                  Express API written in TypeScript
  prisma/                  PostgreSQL schema and migration
  src/controllers/         HTTP validation and responses
  src/services/            Recommendation business rules
  src/repositories/        Prisma data access
  tests/                   Jest unit and PostgreSQL integration tests
render.yaml                Render Blueprint for all three deployed resources
```

The browser sends REST requests to `REACT_APP_API_BASE_URL`. Express validates the request, calls the recommendation service, and persists through Prisma to PostgreSQL. Scores below `-5` cause a recommendation to be deleted. Random selection prefers recommendations scoring above 10 with 70% probability and falls back to all recommendations when that score group is empty.

### API routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Confirm that the API can query its database |
| `GET` | `/recommendations` | Return the ten newest recommendations |
| `POST` | `/recommendations` | Create a recommendation from `name` and `youtubeLink` |
| `GET` | `/recommendations/random` | Return a weighted random recommendation |
| `GET` | `/recommendations/top/:amount` | Return up to 100 highest-scored recommendations |
| `GET` | `/recommendations/:id` | Return one recommendation by positive integer ID |
| `POST` | `/recommendations/:id/upvote` | Increase a recommendation's score |
| `POST` | `/recommendations/:id/downvote` | Decrease its score and delete it below `-5` |

## Requirements

- Node.js 18 or newer (Node 20 is used by the deployment Blueprint)
- npm 8 or newer
- PostgreSQL 12 or newer
- Two terminal sessions for local full-stack development

## Environment variables

No credentials belong in source control. Copy each example file to `.env`; the repository ignores real `.env` files and their variants while explicitly retaining `.env.example` files.

Backend (`back-end/.env`):

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Prisma PostgreSQL connection string; the example targets a local database |
| `PORT` | No | HTTP port, default `5000` |
| `CORS_ORIGIN` | Production | One origin or a comma-separated allowlist; unset allows all origins for local development |
| `MODE` | Tests only | `TEST` enables the database reset route and must not be set in production |

Frontend (`front-end/.env`):

| Variable | Required | Purpose |
| --- | --- | --- |
| `REACT_APP_API_BASE_URL` | Production | Public API origin; local fallback is `http://localhost:5000` |

`REACT_APP_*` values are embedded into the browser bundle and must never contain secrets.

## Local setup

1. Create development and test databases in PostgreSQL, such as `sing_me_a_song` and `sing_me_a_song_test`.
2. Start the API:

   ```bash
   cd back-end
   cp .env.example .env
   npm ci
   npm run db:migrate
   npm run dev
   ```

3. In another terminal, start the frontend:

   ```bash
   cd front-end
   cp .env.example .env
   npm ci
   npm start
   ```

4. Open `http://localhost:3000`. Create a recommendation, vote on it, and verify the Home, Top, and Random routes.

Both packages retain npm lockfiles, so `npm ci` is the reproducible installation path. The backend postinstall step generates the Prisma client automatically.

## Validation

```bash
# Backend production compilation and database-independent tests
cd back-end
npm run build
npm run test:unit

# Backend PostgreSQL integration suite
cp .env.example .env.test
# Change DATABASE_URL to a disposable test database before continuing.
npm run db:migrate -- --schema prisma/schema.prisma
npm run test:integration

# Frontend optimized production bundle
cd ../front-end
npm run build
```

The integration suite truncates the `recommendations` table and must only use a disposable test database. A safe `.env.test` shape is:

```dotenv
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sing_me_a_song_test?schema=public
MODE=TEST
```

## Deployment on Render

`render.yaml` defines a static React site, Node web service, and Render PostgreSQL database. It configures the React Router rewrite, database-backed health checking, deterministic Node version, and secret-safe database URL injection.

1. Push the `H2H-yellow-sing` branch to GitHub.
2. In Render, select **New > Blueprint**, connect this repository, and choose the branch and root `render.yaml`.
3. Supply the two prompted public values:
   - API `CORS_ORIGIN`: the final static-site URL, for example `https://sing-me-a-song-yellow.onrender.com`.
   - Frontend `REACT_APP_API_BASE_URL`: the final API URL, for example `https://sing-me-a-song-yellow-api.onrender.com`.
4. Apply the Blueprint. Render creates the PostgreSQL database and injects its private `connectionString` as `DATABASE_URL`; no database password is stored in Git.
5. If Render assigns suffixed hostnames because a name is unavailable, update both public URL variables and redeploy.
6. Verify `GET https://<api-host>/health`, then create and vote on a recommendation from the deployed frontend. Direct visits to `/top` and `/random` should render through the SPA rewrite.

Free Render web services do not support a separate pre-deploy command. The API therefore runs the idempotent `prisma migrate deploy` command before starting. On a paid plan, moving `npm run db:migrate` to `preDeployCommand` provides cleaner zero-downtime migration behavior.

## Repairs and stability improvements

- Corrected the nonexistent production entry point and added explicit build, Prisma generation, migration, and ESM-aware development scripts.
- Split production TypeScript compilation from test compilation and fixed missing `.js` suffixes in ESM imports.
- Added a database-aware `/health` endpoint and optional comma-separated CORS allowlist.
- Validated IDs and Top limits as positive integers, with a defensive upper bound of 100.
- Returned created and updated records instead of empty mutation responses, restoring frontend success handling and integration tests.
- Fixed the Random route's post-vote refresh so deletion below `-5` cannot leave it requesting a removed record.
- Added client request timeout, valid local API fallback, retryable fetch failures, and mutation-aware form/list refresh behavior.
- Replaced an undeclared online random-video test dependency with offline-safe generated YouTube URLs.
- Corrected integration ordering assertions, POST response coverage, invalid-parameter coverage, mock cleanup, and database disconnect behavior.
- Added secret-safe ignores/environment examples and removed committed macOS metadata.
- Added a reproducible Render Blueprint with PostgreSQL wiring and SPA routing.

## Known limitations and future improvements

- Create React App, Prisma 3, Axios 0.x, Jest 28, Cypress 10, and several transitive packages are aging and emit deprecation warnings. Upgrade them in small, independently tested batches rather than one risky rewrite.
- The original Cypress directory includes duplicated example scaffolding and tests with inconsistent selectors/assumptions. Consolidate it into one maintained end-to-end suite before using Cypress as a release gate.
- Recommendation names are globally unique, and the public API has no authentication, moderation, pagination, or abuse protection.
- Browser feedback relies on native alerts and simple text states. An accessible shared notification/retry component would improve usability.
- Weighted random selection reuses a repository query capped at ten records. A count-and-offset query would sample large datasets more representatively.
- The free deployment runs migrations during service startup. Use Render's paid pre-deploy command or a CI migration job for stronger production rollout guarantees.
