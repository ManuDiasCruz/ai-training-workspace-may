# ai-training-workspace-may

## Sing Me a Song

This branch imports and repairs the sing-me-a-song full-stack project. The app lets users submit YouTube song recommendations, list recent and top recommendations, fetch a random recommendation, and vote recommendations up or down.

The original Create React App documentation is preserved in front-end/README.md.

## Project Structure

- front-end/: React 18 application created with Create React App.
- back-end/: Express + TypeScript API using Prisma and PostgreSQL.
- docker-compose.yml: local PostgreSQL service for development and integration tests.
- docker/postgres/init-test-db.sql: creates the local test database on first compose startup.

## Required Environment Variables

Backend, in back-end/.env:

    DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/sing_me_a_song?schema=public
    PORT=5000
    CORS_ORIGIN=http://localhost:3000

Backend tests, in back-end/.env.test:

    DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/sing_me_a_song_test?schema=public
    MODE=TEST
    PORT=5001

Frontend, in front-end/.env.local for local development:

    REACT_APP_API_BASE_URL=http://localhost:5000

Do not commit real production database URLs or provider credentials. The committed .env.example files contain local-only defaults for the Docker Compose database.

## Local Setup

1. Start PostgreSQL:

       docker compose up -d postgres

2. Install backend dependencies and apply migrations:

       cd back-end
       npm install
       cp .env.example .env
       cp .env.test.example .env.test
       npm run migrate:deploy
       npm run dev

3. Install frontend dependencies and start React:

       cd front-end
       npm install
       cp .env.example .env.local
       npm start

4. Open http://localhost:3000. The API health endpoint is available at http://localhost:5000/health.

## Validation

Backend:

    cd back-end
    npm run build
    npm run test:unit
    npm run test:integration

Frontend:

    cd front-end
    npm run build
    npm test -- --watchAll=false

The React test command is configured with --passWithNoTests because this imported project does not currently include React unit tests.

## Deployment

A simple deployment path is:

1. Provision a managed PostgreSQL database.
2. Deploy back-end/ as a Node web service.
   - Build command: npm install && npm run build
   - Start command: npm run migrate:deploy && npm start
   - Set DATABASE_URL, PORT, and CORS_ORIGIN.
3. Deploy front-end/ as a static site.
   - Build command: npm install && npm run build
   - Publish directory: front-end/build
   - Set REACT_APP_API_BASE_URL to the deployed backend URL.
4. After deployment, verify:
   - GET /health returns { "status": "ok" }.
   - The frontend can list, create, and vote recommendations without CORS or network errors.

## Fixes and Improvements Made

- Imported the original sing-me-a-song frontend and backend into this branch.
- Fixed Prisma CommonJS/ESM interop so Jest and the built Node server can both create the Prisma client.
- Fixed backend production scripts by adding npm run build, correcting npm start, and adding npm run migrate:deploy.
- Added dotenv/config loading for local backend startup.
- Added a backend /health endpoint.
- Added configurable CORS via CORS_ORIGIN.
- Returned the created recommendation from POST /recommendations, including its generated id.
- Validated route params before passing them to Prisma, avoiding invalid-id 500 errors.
- Fixed ESM import extensions in test-only backend modules.
- Removed an undeclared test dependency by generating valid YouTube URLs in the test factory.
- Fixed async Jest rejection assertions and test isolation.
- Prevented Jest from collecting built dist/ files.
- Added Docker Compose setup for local development and integration tests.
- Updated frontend env example and removed a build warning.
- Made the frontend test command pass cleanly when no React tests exist.
- Removed imported .DS_Store artifacts from the branch.

## Known Limitations and Future Improvements

- The frontend has Cypress specs but no maintained React unit test suite.
- The project still uses older dependency versions with reported npm audit vulnerabilities; upgrading should be handled separately because it may require breaking changes.
- Deployment requires external hosting credentials and production environment values that are intentionally not committed.
- The backend test route is gated behind MODE=TEST, but production builds still compile the module; this can be refactored later if the test utility surface grows.
