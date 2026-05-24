# Sing me a Song

`Sing me a Song` is a small full-stack music recommendations app. Users submit YouTube links, browse recent recommendations, upvote or downvote songs, view the top-ranked list, and open a random pick. The repository contains a React frontend in `front-end/`, a Node/Express/TypeScript API in `back-end/`, and PostgreSQL persistence managed by Prisma.

The original Create React App documentation is preserved in `front-end/README.md`. This root README adds the project-specific setup, runtime, and deployment guidance that the copied source snapshot was missing.

## Project layout

```text
.
|- back-end/
|  |- prisma/schema.prisma
|  |- src/app.ts
|  |- src/server.ts
|  `- .env.example
|- front-end/
|  |- src/pages/Timeline/
|  |- src/services/recommendations.js
|  `- .env.example
|- render.yaml
`- README.md
```

## Main application flows

- `POST /recommendations` creates a recommendation with `name` and `youtubeLink`.
- `GET /recommendations` returns the latest 10 recommendations.
- `GET /recommendations/top/:amount` returns the highest-scoring recommendations.
- `GET /recommendations/random` returns a random recommendation, biased toward recommendations above score `10`.
- `POST /recommendations/:id/upvote` increments a recommendation score.
- `POST /recommendations/:id/downvote` decrements a recommendation score and removes the record after it drops below `-5`.
- `GET /health` returns `{ "status": "ok" }` for deployment health checks.

## Local setup

Prerequisites:

- Node.js 18+ recommended
- npm
- PostgreSQL

### 1. Backend

```bash
cd back-end
cp .env.example .env
npm install
npx prisma migrate deploy
npm run dev
```

Required backend environment variables:

```env
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/sing_me_a_song
PORT=5000
CORS_ORIGIN=http://localhost:3000
MODE=DEVELOPMENT
```

`CORS_ORIGIN` accepts one or more comma-separated frontend origins. Leave secrets in `.env` or your hosting provider settings; do not commit real credentials.

### 2. Frontend

```bash
cd front-end
cp .env.example .env
npm install
npm start
```

Required frontend environment variable:

```env
REACT_APP_API_BASE_URL=http://localhost:5000
```

The frontend runs on `http://localhost:3000` by default. Keep `REACT_APP_API_BASE_URL` aligned with the API port you choose.

## Validation

Useful checks after the database and dependencies are available:

```bash
cd back-end
npx prisma migrate deploy
npm run build
curl http://localhost:5000/health
```

Then validate the browser flow:

1. Create a recommendation from Home.
2. Upvote and downvote it.
3. Open Top and confirm score ordering updates.
4. Open Random and confirm the UI shows an empty state instead of getting stuck when there are no recommendations.

## Deployment

`render.yaml` provides a simple Render blueprint:

- `sing-me-a-song-api`: Node web service rooted at `back-end/`
- `sing-me-a-song-web`: static React site rooted at `front-end/`

Set these values in the hosting dashboard instead of committing them:

```env
# API service
DATABASE_URL=<managed-postgresql-url>
CORS_ORIGIN=https://<frontend-host>

# Static frontend service
REACT_APP_API_BASE_URL=https://<api-host>
```

The API build path runs Prisma generation, TypeScript compilation, and `prisma migrate deploy`. The health check path is `/health`.

## Fixes and stability improvements made

- Repaired the backend runtime path by adding an explicit build script and changing production start from the nonexistent `dist/index.js` to `dist/server.js`.
- Replaced the broken legacy `ts-node` dev path with `tsx watch`, which works on current Node releases.
- Added local `.env` loading in the backend entrypoint.
- Added `/health` and made CORS configurable via `CORS_ORIGIN`.
- Added safe route parameter validation so invalid IDs or `top/:amount` values return `422` instead of bubbling into Prisma/runtime errors.
- Changed `POST /recommendations` to return the created row with status `201`.
- Removed an unused frontend-only dependency from the backend package manifest.
- Added a frontend API fallback URL and corrected `front-end/.env.example`.
- Prevented the Random page from sitting on `Loading...` forever when the database is empty.
- Kept failed create/upvote/downvote requests from clearing state or triggering unhandled promise rejections in the UI flow.
- Fixed ESM import paths in the test-only reset path and removed a missing random YouTube test helper dependency.
- Added root ignore rules, this README, backend env docs, and a deployment blueprint.

## Known limitations and future improvements

- There is no authentication, abuse prevention, or rate limiting.
- Failure handling in the frontend still uses browser alerts instead of inline error messaging.
- The test suite in the copied source snapshot is inconsistent and should be rebuilt around deterministic fixtures before relying on CI as a release gate.
- PostgreSQL is required; there is no lightweight local fallback for first-time contributors.
- Production deployment still needs actual hosting credentials and real environment values supplied outside the repository.
