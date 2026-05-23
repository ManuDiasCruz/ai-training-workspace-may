# Sing me a Song

`Sing me a Song` is a small full-stack recommendations app. Users submit YouTube music links, browse the latest recommendations, vote songs up or down, and open a random pick. The application is split into a React frontend in `front-end/` and a Node/Express/TypeScript API in `back-end/`, with PostgreSQL managed through Prisma.

The original Create React App documentation is preserved in `front-end/README.md`; this root README adds the project-specific setup and deployment guidance that was missing.

## Project layout

```text
.
|- back-end/
|  |- prisma/schema.prisma          # PostgreSQL schema and migration history
|  |- src/app.ts                    # Express app, CORS, health route, API routes
|  |- src/server.ts                 # API entrypoint
|  `- .env.example                  # Safe backend environment template
|- front-end/
|  |- src/services/recommendations.js
|  |- src/pages/Timeline/*          # Home, Top, and Random flows
|  `- .env.example                  # Safe frontend environment template
|- render.yaml                      # Render deployment blueprint
`- README.md
```

## Main flows

- `POST /recommendations` creates a recommendation with `name` and `youtubeLink`.
- `GET /recommendations` returns the latest 10 recommendations.
- `GET /recommendations/top/:amount` returns the highest-scoring recommendations.
- `GET /recommendations/random` returns a random recommendation, biased toward high scores.
- `POST /recommendations/:id/upvote` increments the score.
- `POST /recommendations/:id/downvote` decrements the score and removes the row once it drops below `-5`.
- `GET /health` is available for deployment health checks.

## Local setup

Prerequisites:

- Node.js 16+ or 18+
- npm
- PostgreSQL

1. Backend

```bash
cd back-end
cp .env.example .env
npm install
npx prisma migrate dev
npm run dev
```

Backend environment variables:

```env
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/sing_me_a_song
PORT=5000
CORS_ORIGIN=http://localhost:3000
MODE=DEVELOPMENT
```

2. Frontend

```bash
cd front-end
cp .env.example .env
npm install
npm start
```

Frontend environment variables:

```env
REACT_APP_API_BASE_URL=http://localhost:5000
```

The frontend runs on `http://localhost:3000` by default. Keep `REACT_APP_API_BASE_URL` aligned with the backend `PORT`.

## Validation

Recommended checks once dependencies and a database are available:

```bash
cd back-end
npx prisma migrate deploy
npm run build
curl http://localhost:5000/health
```

Then verify the user flow in the browser:

1. Create a recommendation from Home.
2. Upvote and downvote it.
3. Open Top and confirm the score ordering updates.
4. Open Random and confirm the UI shows a clean empty state when the database has no recommendations.

## Deployment

`render.yaml` provides a simple two-service Render setup:

- `sing-me-a-song-api`: Node web service rooted at `back-end/`
- `sing-me-a-song-web`: static React site rooted at `front-end/`

Configure these values in the Render dashboard instead of committing them:

- API service: `DATABASE_URL`, `CORS_ORIGIN`
- Static site: `REACT_APP_API_BASE_URL`

Suggested production values:

```env
# API service
DATABASE_URL=<managed-postgresql-url>
CORS_ORIGIN=https://<frontend-host>

# Static frontend site
REACT_APP_API_BASE_URL=https://<api-host>
```

The API build command runs Prisma generation, TypeScript compilation, and `prisma migrate deploy`. The health check path is `/health`.

## Fixes and stability improvements

- Fixed the backend production entrypoint: the source app started `dist/index.js`, but the compiled file is `dist/server.js`.
- Added a backend build script that runs Prisma generation and TypeScript compilation.
- Added `dotenv/config` loading in the backend entrypoint for local `.env` files.
- Added `/health` for deployment health checks.
- Made CORS configurable through `CORS_ORIGIN`.
- Added route parameter validation so invalid IDs or `top/:amount` values return `422` instead of bubbling into runtime errors.
- Changed `POST /recommendations` to return the created row with `201`.
- Fixed ESM import paths in the test-only reset flow.
- Added a local API fallback and corrected `front-end/.env.example`.
- Fixed the Random page so an empty database no longer leaves the UI stuck on `Loading...`.
- Removed unused backend `react-player` dependency from the API manifest.
- Added safe ignore rules for secrets, `node_modules`, and build output.
- Added `render.yaml` and this README to make local setup and deployment reproducible.

## Known limitations and future improvements

- The project currently has no authentication, abuse prevention, or rate limiting.
- Observability is minimal; structured logging and error reporting would make production debugging easier.
- The source repository carried incomplete/broken Cypress coverage and an unstable backend test factory that depended on a missing random YouTube package. Those tests should be rebuilt around deterministic fixtures before treating CI as authoritative.
- PostgreSQL is required; there is no SQLite fallback for first-time contributors.
- The frontend shows browser `alert()` calls for request failures instead of inline error messaging.
- The original source snapshot referenced generated CRA icon assets that were not part of the copied text tree. The app runs without them, but branded icons can be restored later.
