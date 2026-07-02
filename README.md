# Sing me a Song

Sing me a Song is a full-stack music recommendation app. Visitors can submit YouTube songs, browse the latest recommendations, vote songs up or down, view the top ten, and request a weighted random recommendation. The React frontend calls an Express API backed by PostgreSQL through Prisma.

The original Create React App documentation remains available at [`front-end/README.md`](front-end/README.md).

## Project structure and flow

```text
front-end/   React 18 UI, Axios API client, React Router, styled-components
back-end/    Express API, TypeScript, Prisma client and PostgreSQL migrations
render.yaml  One-service Render deployment plus managed PostgreSQL
```

In development, the frontend runs at `http://localhost:3000` and calls the API at `http://localhost:5000`. In production, Express serves the compiled React application and the API from one origin. Requests flow through the controller, service, repository, and Prisma layers before reaching PostgreSQL.

## Requirements

- Node.js 20 or 22 (the deployment is pinned to the version in `.node-version`)
- npm
- PostgreSQL 13 or newer

## Local setup

1. Create a PostgreSQL database, such as `sing_me_a_song`.
2. Install and configure the backend:

   ```bash
   cd back-end
   npm ci
   cp .env.example .env
   npm run db:migrate
   npm run dev
   ```

3. In a second terminal, install and start the frontend:

   ```bash
   cd front-end
   npm ci
   cp .env.example .env
   npm start
   ```

On PowerShell, use `Copy-Item .env.example .env` instead of `cp`. Replace the example PostgreSQL URL with your own local connection details. Never commit `.env` files; both apps ignore them while keeping the safe `.env.example` files tracked.

### Environment variables

| Variable | App | Required | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Backend | Yes | PostgreSQL connection string used by Prisma. |
| `PORT` | Backend | No | HTTP port; defaults to `5000`. Hosting platforms usually inject this. |
| `CORS_ORIGIN` | Backend | No | Comma-separated allowed origins for a separately hosted frontend. Omit for same-origin production hosting. |
| `MODE` | Backend | No | Set to `TEST` only to expose the test reset route. Never enable it in production. |
| `REACT_APP_API_BASE_URL` | Frontend | Development only | API origin, normally `http://localhost:5000`. Leave unset for the unified production service. |

### Useful commands

```bash
npm test --prefix back-end
npm run test:integration --prefix back-end  # requires back-end/.env.test and an isolated test database
npm run build --prefix back-end
npm run build --prefix front-end
```

For a local production-style run, build the frontend and backend, set `DATABASE_URL` and `NODE_ENV=production`, then run `npm start --prefix back-end`. The backend serves `front-end/build` and supports direct navigation to `/top` and `/random`.

## API overview

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Confirms the server can query PostgreSQL. |
| `GET` | `/recommendations` | Returns the ten newest recommendations. |
| `POST` | `/recommendations` | Creates a named YouTube recommendation. |
| `GET` | `/recommendations/random` | Returns a weighted random recommendation. |
| `GET` | `/recommendations/top/:amount` | Returns up to 100 recommendations ordered by score. |
| `GET` | `/recommendations/:id` | Returns one recommendation. |
| `POST` | `/recommendations/:id/upvote` | Adds one vote. |
| `POST` | `/recommendations/:id/downvote` | Removes one vote and deletes scores below -5. |

## Deployment

The included Render Blueprint creates one Node web service. The build installs both apps, compiles React and TypeScript, and the start command applies committed Prisma migrations before starting Express. Supply a direct PostgreSQL connection string from Render Postgres, Neon, or another compatible provider when the Blueprint asks for `DATABASE_URL`.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FManuDiasCruz%2Fai-training-workspace-may%2Ftree%2FH2H-red-sing)

To deploy manually in Render:

1. Provision PostgreSQL. For Prisma 3 migrations on Neon, use its direct (non-pooler) connection string with SSL enabled.
2. Create a Blueprint from this repository and select branch `H2H-red-sing`.
3. Enter the database URL as the secret `DATABASE_URL` value when prompted, review `render.yaml`, and apply the Blueprint.
4. Wait for the migration, build, and health check to complete.
5. Open the generated `onrender.com` URL and verify create, list, vote, top, and random flows.

No database password or connection URL is committed. Render stores `DATABASE_URL` as an environment secret at deploy time.

## Repairs and improvements

- Corrected the backend TypeScript build output and production start path.
- Added runtime `.env` loading, safe environment examples, Node version bounds, and deploy-time Prisma migration commands.
- Fixed ESM imports that broke compiled execution and repaired the unit-test setup.
- Added request parameter validation and race-safe duplicate recommendation handling.
- Added a PostgreSQL-aware health check and production SPA/static serving.
- Corrected frontend API configuration, loading/error/retry states, and form submission behavior so failed requests no longer clear user input.
- Added production metadata, a reproducible CI workflow, and Render infrastructure configuration.

## Known limitations and future work

- Free Render services can cold-start after inactivity, and free database retention/limits should be reviewed before production use.
- The app has no authentication, moderation, or rate limiting; it should not be exposed to untrusted high-volume traffic without those controls.
- Several original dependencies are old or deprecated. Upgrade them in focused changes with regression testing instead of a broad rewrite.
- Integration tests require an isolated PostgreSQL database and are intentionally excluded from the default unit-test command.
- YouTube playback depends on third-party availability, embedding permissions, and browser privacy settings.
