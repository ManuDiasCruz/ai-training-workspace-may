# Sing Me a Song

Sing Me a Song is a small full-stack recommendation board for sharing YouTube songs, voting recommendations up or down, browsing the ten highest-scored entries, and asking the application to select a weighted random song. This repository contains the original React frontend and Express/TypeScript/Prisma backend, with targeted repairs that make the project buildable, configurable, and ready for a reproducible Render deployment.

The source project's original Create React App notes remain in [`front-end/README.md`](front-end/README.md).

## Project structure and flow

```text
front-end/                 React 18 single-page application
  src/services/            Axios client and recommendation requests
  src/hooks/api/            Async state wrappers for API calls
  src/pages/Timeline/       Home, Top, and Random pages
back-end/                  Express API written in TypeScript
  prisma/                   PostgreSQL schema and migration
  src/controllers/          Request validation and HTTP responses
  src/services/             Recommendation business rules
  src/repositories/         Prisma data access
  tests/                    Jest unit and PostgreSQL-backed integration tests
render.yaml                Render Blueprint for web/API/PostgreSQL services
```

The browser calls the REST API configured by `REACT_APP_API_BASE_URL`. Express validates each request, delegates recommendation rules to the service layer, and persists data through Prisma and PostgreSQL.

### API summary

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API and database readiness check |
| `GET` | `/recommendations` | Ten most recently created songs |
| `POST` | `/recommendations` | Create a song with `name` and `youtubeLink` |
| `GET` | `/recommendations/random` | Weighted random song (70% preference for score above 10) |
| `GET` | `/recommendations/top/:amount` | Highest scored songs, up to 100 |
| `GET` | `/recommendations/:id` | One song by positive numeric ID |
| `POST` | `/recommendations/:id/upvote` | Increase the score |
| `POST` | `/recommendations/:id/downvote` | Decrease the score and delete below -5 |

## Requirements

- Node.js 18 or newer and npm
- PostgreSQL 12 or newer
- Two terminal sessions for local full-stack development

## Environment variables

No real credentials are stored in the repository. Copy the example files and keep local `.env` files untracked.

Backend (`back-end/.env`):

| Variable | Required | Example / purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | `postgresql://postgres:postgres@localhost:5432/sing_me_a_song?schema=public` |
| `CORS_ORIGIN` | Production | Comma-separated browser origins, such as `http://localhost:3000` |
| `PORT` | No | Defaults to `5000` |
| `MODE` | No | Set to `TEST` only to enable the test reset route |

Frontend (`front-end/.env`):

| Variable | Required | Example / purpose |
| --- | --- | --- |
| `REACT_APP_API_BASE_URL` | Production | Public API origin; local default is `http://localhost:5000` |

## Local setup

1. Create the PostgreSQL databases used by development and integration tests (for example, `sing_me_a_song` and `sing_me_a_song_test`).
2. Configure and start the API:

   ```bash
   cd back-end
   cp .env.example .env
   npm ci
   npm run db:migrate
   npm run dev
   ```

3. In a second terminal, configure and start the React application:

   ```bash
   cd front-end
   cp .env.example .env
   npm ci
   npm start
   ```

4. Open `http://localhost:3000`. Confirm that creating a recommendation, voting, Top, and Random all call the API at `http://localhost:5000`.

`npm ci` is preferred because both packages include committed npm lockfiles. The backend `postinstall` script generates the Prisma client automatically.

## Validation and tests

```bash
# Backend production compile
cd back-end
npm run build

# Backend unit tests (no database required)
npm run test:unit

# Backend integration tests (requires back-end/.env.test and a disposable test DB)
npm run test:integration

# Frontend production bundle
cd ../front-end
npm run build
```

Use a dedicated database in `back-end/.env.test`; the integration suite truncates tables. A safe example is:

```dotenv
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sing_me_a_song_test?schema=public
MODE=TEST
```

## Deployment on Render

The root `render.yaml` is a Blueprint for a static React site, Node/Express service, and Render PostgreSQL database. It also configures the React Router rewrite, database migrations before API startup, and `/health` monitoring. These settings follow Render's documented Blueprint, Express, Create React App, and Prisma deployment patterns.

1. Push the intended branch to GitHub and choose **New > Blueprint** in Render.
2. Connect this repository and select `render.yaml`.
3. When prompted, set:
   - Backend `CORS_ORIGIN` to the final frontend URL, for example `https://sing-me-a-song-blue.onrender.com`.
   - Frontend `REACT_APP_API_BASE_URL` to the final API URL, for example `https://sing-me-a-song-blue-api.onrender.com`.
4. Apply the Blueprint. Render supplies `DATABASE_URL` directly from the managed database without exposing it in source control.
5. After both services are live, open `/health` on the API, then create and vote on a song from the deployed frontend. If a Render-generated hostname differs from the example, update the two public URL variables and redeploy.

## Repairs and stability improvements

- Corrected the backend production entry point and added explicit build, Prisma generation, migration, and development commands.
- Split production TypeScript compilation from the test compilation context and fixed ESM imports that prevented the backend from compiling reliably.
- Removed a missing third-party random-video test dependency and made generated test recommendations unique and offline-safe.
- Added positive-integer validation for ID/limit routes, with a defensive upper bound on Top queries.
- Added an API/database health endpoint and optional environment-driven CORS allowlist.
- Added valid local environment examples, a frontend API fallback/timeout, and secret-safe repository ignores.
- Corrected async frontend behavior so forms clear and lists refresh only after successful mutations; failed fetches now show usable states instead of indefinite loading screens.
- Added stable selectors for the original voting end-to-end scenarios and removed a production-build lint warning.
- Added infrastructure-as-code for the frontend, API, and database, including migrations and SPA routing.

## Known limitations and future work

- The project depends on Create React App, Prisma 3, Axios 0.x, Jest 28, Cypress 10, and other aging packages with deprecation warnings. Upgrade these in small, independently tested batches.
- The source repository includes legacy/duplicated Cypress scaffolding with inconsistent custom commands. Consolidate it into one maintained browser suite before treating Cypress as a release gate.
- The app uses native `alert` calls and basic loading/error text. A shared accessible notification and retry component would improve feedback.
- Recommendation names are globally unique and there is no authentication, moderation, pagination, or abuse protection. These are important before broader public use.
- Random recommendation weighting currently loads a maximum of ten eligible rows because it reuses the timeline repository method. A dedicated count/offset query would produce a more representative random result on larger datasets.

