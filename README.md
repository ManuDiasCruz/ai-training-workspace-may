# Sing me a Song

Sing me a Song is a full-stack music recommendation app. Visitors can submit YouTube links, browse the ten newest recommendations, upvote or downvote songs, view the top ten, and request a weighted random recommendation.

The project keeps the original React, Express, TypeScript, Prisma, and PostgreSQL architecture. In development, React and the API run separately. In production, Express serves the compiled React app and API from one origin, which removes deployment-time CORS coupling.

## Application flow

1. The React client calls the recommendation API.
2. Express validates the request and delegates to the recommendation service.
3. Prisma reads or updates PostgreSQL.
4. The API returns the current recommendation data and the UI refreshes the relevant view.

API routes:

- `GET /health`
- `GET|POST /recommendations`
- `GET /recommendations/random`
- `GET /recommendations/top/:amount`
- `GET /recommendations/:id`
- `POST /recommendations/:id/upvote`
- `POST /recommendations/:id/downvote`

## Requirements

- Node.js 18–20 (Node 20.18.0 is used in CI and deployment)
- npm 9 or newer
- PostgreSQL 14 or newer

## Local setup

1. Install the locked frontend and backend dependencies:

   ```bash
   npm run install:all
   ```

2. Copy `back-end/.env.example` to `back-end/.env` and update `DATABASE_URL` for your local PostgreSQL instance.

3. Create the database named in `DATABASE_URL`, then apply its migration:

   ```bash
   npm --prefix back-end run db:deploy
   ```

4. Start the API and frontend in separate terminals:

   ```bash
   npm run dev:api
   npm run dev:web
   ```

5. Open `http://localhost:3000`. The API defaults to `http://localhost:5000`.

To run the backend test suite, copy `back-end/.env.test.example` to `back-end/.env.test`, create the test database in that connection string, and run `npm test`. The integration tests truncate only the configured test database.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Backend | PostgreSQL connection string used by Prisma. |
| `PORT` | No | API port; defaults to `5000` locally and is supplied by the host. |
| `MODE` | No | Set to `TEST` only to expose the test reset route. |
| `SERVE_FRONTEND` | No | Set to `true` in production so Express serves `front-end/build`. |
| `CORS_ORIGIN` | No | Comma-separated origin allowlist. If omitted, the API permits all origins. |
| `REACT_APP_API_BASE_URL` | No | Frontend API URL. Defaults to `http://localhost:5000` in development and the current origin in production. |
| `CYPRESS_BASE_URL` | No | Cypress frontend URL; defaults to `http://localhost:3000`. |
| `CYPRESS_API_URL` | No | Cypress API URL; defaults to `http://localhost:5000`. |

Real `.env` files are ignored. Commit only the provided examples, never credentials or tokens.

## Validation commands

```bash
npm run build
npm run test:unit
npm test
npm run test:e2e
```

`npm test` and `npm run test:e2e` require the test PostgreSQL database. Cypress also requires the API to run with `MODE=TEST` and the frontend development server to be running.

## Deployment

The included `render.yaml` defines a Render Blueprint with one Node web service and one private PostgreSQL database. The web service installs from both lockfiles, builds the API and React client, applies Prisma migrations before deployment, serves both layers from one HTTPS origin, and checks `/health` before it is marked healthy.

To deploy:

1. Push branch `731-ceh-singmeasong` to GitHub.
2. In Render, create a new Blueprint from this repository and select `render.yaml`.
3. Review the two free resources and apply the Blueprint.
4. Wait for `/health` to pass, then verify create, vote, top, and random flows at the generated `onrender.com` URL.

Render's free web service can cold-start after inactivity, and a free Render PostgreSQL database expires after 30 days. Use paid resources or another managed PostgreSQL provider for a durable production deployment.

## Repairs and improvements

- Corrected the nonexistent backend production entrypoint and added a deterministic production build.
- Added environment loading, safe example configuration, graceful shutdown, database-backed health checks, request size limits, and optional CORS allowlisting.
- Repaired ESM runtime imports, invalid route parameter handling, structured API errors, and duplicate-insert race handling.
- Fixed broken unit/integration fixtures and assertions, added teardown, and added health/validation coverage.
- Made failed frontend requests observable and retryable instead of silently continuing.
- Preserved form values on failed submissions and made create/vote controls accessible and state-aware.
- Replaced the disconnected Cypress specs with a bounded main-flow suite.
- Added repeatable root scripts, CI with PostgreSQL, and infrastructure-as-code deployment.

## Known limitations and future improvements

- Create React App, Prisma 3, Jest 28, Cypress 10, and several transitive dependencies are old. Upgrade them in a dedicated change with regression testing rather than mixing a broad migration into this repair.
- The app has no authentication, moderation, abuse controls, or rate limiting.
- Free hosting is suitable for demonstration, not durable production data.
- YouTube availability and embedding policies are controlled externally, so individual videos can become unavailable.
- The random selection algorithm intentionally favors recommendations with scores above 10 but is not statistically tested.

The original Create React App documentation remains preserved in [`front-end/README.md`](front-end/README.md).
