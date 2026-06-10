# Sing Me a Song

> Branch `fable-29f0b72b-sing-me-a-song` of **ai-training-workspace-may** — a repaired
> copy of [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song).
> The original front-end Create React App docs are preserved in
> [`front-end/README.md`](front-end/README.md).

Anonymous song-recommendation app: anyone can recommend a YouTube song, upvote or
downvote recommendations, and browse the feed, the top-scored list, or a random pick.
A recommendation whose score drops below **-5** is removed automatically.

## Stack

| Layer     | Tech                                                                  |
|-----------|-----------------------------------------------------------------------|
| Back-end  | Node.js, TypeScript (ESM), Express, Prisma 3, PostgreSQL              |
| Front-end | React 18 (Create React App), styled-components, axios, react-player   |
| Tests     | Jest + Supertest (unit/integration), Cypress (E2E)                    |

## Project structure

```
back-end/    Express + Prisma API (TypeScript, native ESM)
front-end/   React SPA + Cypress E2E suite
docker-compose.yml   Full-stack deployment (db + api + nginx-served SPA)
render.yaml          One-click Render.com blueprint (cloud alternative)
```

## API

| Method | Route                          | Description                                  |
|--------|--------------------------------|----------------------------------------------|
| POST   | `/recommendations`             | Create `{ name, youtubeLink }` (name unique) |
| GET    | `/recommendations`             | Last 10 recommendations, newest first        |
| GET    | `/recommendations/random`      | Weighted random pick (70% score > 10)        |
| GET    | `/recommendations/top/:amount` | Top `:amount` by score                       |
| GET    | `/recommendations/:id`         | One recommendation                           |
| POST   | `/recommendations/:id/upvote`  | Score +1                                     |
| POST   | `/recommendations/:id/downvote`| Score -1 (deleted when score < -5)           |
| DELETE | `/tests/reset`                 | Truncate data — **only when `MODE=TEST`**    |

Errors: `409` duplicate name, `422` invalid body, `404` unknown id.

## Running locally

Requirements: Node.js 18+ (tested on 22), npm, and a PostgreSQL instance
(`docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15-alpine` works).

### Back-end

```bash
cd back-end
npm install
cp .env.example .env          # adjust DATABASE_URL if needed
npx prisma migrate deploy     # create the schema
npm run dev                   # http://localhost:5000
```

Production build: `npm run build && npm start`.

### Front-end

```bash
cd front-end
npm install
cp .env.example .env          # REACT_APP_API_BASE_URL must point at the API
npm start                     # http://localhost:3000
```

### Environment variables

`back-end/.env` (template: [`back-end/.env.example`](back-end/.env.example)):

| Variable       | Meaning                                                        |
|----------------|----------------------------------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string used by Prisma                    |
| `PORT`         | API port (default `5000`)                                      |
| `MODE`         | `TEST` mounts `DELETE /tests/reset`; use `DEV`/`PROD` otherwise|

`back-end/.env.test` (template: `.env.test.example`) must point at a **disposable**
database — the test runner truncates it and `npm test` runs `prisma migrate reset`.

`front-end/.env` (template: `.env.example`):

| Variable                  | Meaning                                   |
|---------------------------|-------------------------------------------|
| `REACT_APP_API_BASE_URL`  | URL the browser uses to reach the API     |

No real credentials are committed — only `*.example` templates.

## Tests

```bash
# back-end (needs .env.test): 26 tests
cd back-end
npm test                 # resets the test DB, then unit + integration
npm run test:unit
npm run test:integration

# front-end E2E: 10 tests. Requires the app AND the API running with MODE=TEST
cd back-end && npm run dev:test          # terminal 1 — API in TEST mode
cd front-end && npm start                # terminal 2 — React app
cd front-end && npx cypress run          # terminal 3 — headless E2E
```

Cypress defaults to app `http://localhost:3000` / API `http://localhost:5000`;
override with `CYPRESS_BASE_URL` and `CYPRESS_apiUrl`.

## Deployment

### Docker Compose (self-hosted — what this branch was verified with)

```bash
docker compose up -d --build
# frontend http://localhost:3000 — API http://localhost:5000
```

Configurable through environment variables: `FRONTEND_PORT`, `BACKEND_PORT`,
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and `API_PUBLIC_URL` (the
URL the **browser** uses for the API — CRA bakes it in at image build time):

```bash
BACKEND_PORT=5100 FRONTEND_PORT=8100 API_PUBLIC_URL=http://localhost:5100 \
  docker compose up -d --build
```

The backend container applies pending Prisma migrations on start
(`prisma migrate deploy`), so a fresh stack is usable immediately.

### Render.com (cloud)

[`render.yaml`](render.yaml) provisions the API (Node web service), the front-end
(static site with SPA rewrite) and a free PostgreSQL instance: Render dashboard →
*New* → *Blueprint* → select this repo/branch. After the first deploy, point the
front-end's `REACT_APP_API_BASE_URL` at the API's public URL and rebuild.

## Fixes and improvements in this branch

Runtime/bugs (details in the git history — each fix is its own commit):

1. **Server could not start**: two relative imports lacked the `.js` extension
   required by native ESM, crashing the app at boot; the dev runner (ts-node 10
   ESM loader) is broken on Node ≥ 20 and was replaced with `tsx`.
2. **`npm start` pointed at `dist/index.js`**, which never existed; there was no
   build script at all. Added `npm run build` (prisma generate + tsc scoped to
   `src/`) and fixed the entry to `dist/server.js`.
3. **`.env` was never loaded** (dotenv was installed but never invoked), so `PORT`
   and `MODE` were silently ignored. Added `import "dotenv/config"`.
4. **Back-end test suite crashed on import**: a factory `require()`d a package
   that is not in `package.json` (inside an ESM module, where `require` doesn't
   exist). Three tests had broken assertions (reading `body.id` from an empty 201
   response, wrong expected ordering, a unit test that silently hit the real DB).
   All 26 tests now pass.
5. **Cypress suite was unrunnable**: reset command called `DELETE /reset` instead
   of `DELETE /tests/reset`, specs referenced undefined variables and selectors
   that didn't exist in the React components, and the "max 10 posts" test created
   invalid links that the API rejects. Repaired, made app/API URLs configurable,
   added the missing `data-identifier` attributes, ported the orphaned vote/render
   specs into working tests and removed dead/example spec files. All 10 E2E pass.
6. **`front-end/.env.example` was the truncated value `http://`** — completed, and
   added the missing back-end `.env.example`/`.env.test.example`.
7. Removed `react-player` (a React component library) from the **server**
   dependencies, the dangling `prisma.seed` config pointing at a non-existent
   file, committed `.DS_Store` files, and a CRA build warning.
8. Added Dockerfiles, nginx SPA config, `docker-compose.yml` and `render.yaml`
   for deployment.

## Known limitations / future improvements

- **Prisma 3.13 and CRA 5 are dated**; upgrading Prisma to 5.x and migrating off
  deprecated faker APIs would future-proof the stack.
- **No CI pipeline** — the Jest and Cypress suites are local-only today.
- **No pagination** beyond the fixed "last 10" feed; no search.
- The random endpoint returns `404` when the database is empty — the Random page
  surfaces a permanent "Loading..." state instead of a friendly empty state.
- `GET /recommendations/top/:amount` does not validate `:amount` (a non-numeric
  value yields a Prisma error / 500).
- E2E suite needs the API in `MODE=TEST`; a seeding endpoint would allow the
  score-distribution scenarios from the original (removed) spec files.
