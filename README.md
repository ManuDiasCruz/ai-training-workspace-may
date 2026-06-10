# Sing Me A Song

Sing Me A Song is a full-stack music recommendation app. Users can submit YouTube links, view recent recommendations, vote songs up or down, see top-ranked songs, and open a random recommendation.

The original Create React App documentation is preserved in front-end/README.md. This root README adds the project-specific setup, environment, validation, and deployment notes.

## Project Overview

- back-end/: Express, TypeScript, Prisma, and PostgreSQL API.
- front-end/: React client built with Create React App.
- back-end/prisma/: Prisma schema and migration history.
- docker-compose.yml: local PostgreSQL service with a test database init script.
- render.yaml: Render Blueprint for a static frontend, Node backend, and managed PostgreSQL database.

## Main Application Flow

- POST /recommendations creates a recommendation and returns the created row.
- GET /recommendations lists the latest 10 recommendations.
- GET /recommendations/top/:amount lists highest-scored recommendations.
- GET /recommendations/random returns a weighted random recommendation.
- POST /recommendations/:id/upvote increments score.
- POST /recommendations/:id/downvote decrements score and deletes rows below -5.
- GET /health returns API health for deployment checks.

## Local Setup

Prerequisites:

- Node.js 20+ recommended
- npm
- Docker, or a reachable PostgreSQL server

Start PostgreSQL with Docker:

~~~bash
docker compose up -d postgres
~~~

Backend:

~~~bash
cd back-end
cp .env.example .env
cp .env.test.example .env.test
npm ci
npm run build
npx prisma migrate deploy
npm start
~~~

Frontend:

~~~bash
cd front-end
cp .env.example .env
npm ci
npm start
~~~

Default local URLs:

- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- Health check: http://localhost:5000/health

## Environment Variables

Backend (back-end/.env):

~~~env
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/sing_me_a_song
PORT=5000
CORS_ORIGIN=http://localhost:3000
MODE=DEV
~~~

Backend tests (back-end/.env.test):

~~~env
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/sing_me_a_song_test
PORT=5001
CORS_ORIGIN=http://localhost:3000
MODE=TEST
~~~

Frontend (front-end/.env):

~~~env
REACT_APP_API_BASE_URL=http://localhost:5000
~~~

Do not commit real production credentials. Local .env files are ignored; safe examples are committed.

## Validation

Backend:

~~~bash
cd back-end
npm test
npm run build
~~~

Frontend:

~~~bash
cd front-end
npm run build
~~~

Manual smoke flow:

1. Open the frontend.
2. Create a recommendation with a valid YouTube URL.
3. Upvote and downvote the recommendation.
4. Check Top and Random pages.
5. Verify GET /health returns {"status":"ok"}.

## Deployment

The included render.yaml is the simplest production path for this stack:

- Render Postgres database
- Render Node web service for back-end/
- Render static site for front-end/

Render will require host-specific values:

- API service CORS_ORIGIN: public frontend URL
- Frontend static site REACT_APP_API_BASE_URL: public API URL

Manual equivalent:

1. Provision PostgreSQL and set DATABASE_URL on the backend host.
2. Deploy back-end/ as a Node service.
3. Backend build command: npm ci && npm run build.
4. Backend start command: npm run deploy:start.
5. Deploy front-end/ as a static React site.
6. Frontend build command: npm ci && npm run build.
7. Configure SPA fallback to index.html for /top and /random.
8. Set backend CORS to the public frontend origin.

## Fixes And Improvements Made

- Fixed backend production start path from missing dist/index.js to dist/server.js.
- Added a backend build script with Prisma generation and TypeScript compilation.
- Added local dotenv loading for backend runtime.
- Fixed Prisma CommonJS/ESM imports under Jest and Node.
- Fixed broken ESM imports in the test reset flow.
- Made POST /recommendations return the created recommendation.
- Added configurable CORS and a /health endpoint.
- Added numeric route validation for IDs and top-list amount.
- Fixed test factories to avoid an undeclared random YouTube package.
- Fixed unit tests that were not awaiting rejected promises.
- Corrected integration expectations for latest-first listing.
- Fixed frontend API base URL example and added a local fallback.
- Added Random page empty/error handling.
- Added vote element identifiers used by E2E smoke coverage.
- Removed an unused backend react-player dependency.
- Added Docker and Render setup files plus safe env examples.

## Known Limitations And Future Improvements

- The dependency tree is legacy CRA/Prisma and still reports npm audit findings.
- Cypress specs from the source snapshot include stale scaffold tests and should be rebuilt before being used as CI gates.
- Frontend error handling still relies on browser alerts in several flows.
- The app has no authentication, rate limiting, moderation, or abuse prevention.
- Production deployment needs external host credentials and managed environment variables configured outside git.
