# 🎵 Sing me a Song

A full-stack song-recommendation app: anyone can post a YouTube link, vote it up
or down, and browse recommendations three ways (latest, top-scored, random). A
recommendation whose score drops below **-5** is deleted automatically.

> This branch (`731-fh-singmeasong`) imports the project from
> [`ManuDiasCruz/sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song)
> and repairs it so it installs, runs, passes its tests, builds and deploys.
> See [Fixes and improvements](#fixes-and-improvements) for the full list.
> (The `README` of the workspace's original project was preserved as
> [`PARROT-GAME-README.md`](PARROT-GAME-README.md); the front-end's original
> Create React App docs live in [`front-end/README.md`](front-end/README.md).)

**Live front-end:** <https://manudiascruz.github.io/singmeasong-731-deploy/>

## Project structure

| Path | What it is |
| --- | --- |
| `back-end/` | Node + Express + TypeScript REST API, Prisma ORM, PostgreSQL |
| `front-end/` | React 18 (Create React App), styled-components, react-player |
| `render.yaml` | Render blueprint that provisions the API + PostgreSQL database |

### API routes

| Method & path | Purpose |
| --- | --- |
| `POST /recommendations` | Create a recommendation (`name`, `youtubeLink`) |
| `GET /recommendations` | Latest 10 recommendations |
| `GET /recommendations/random` | One random recommendation (70% chance score > 10) |
| `GET /recommendations/top/:amount` | Top `:amount` by score |
| `GET /recommendations/:id` | One recommendation by id |
| `POST /recommendations/:id/upvote` | Score +1 |
| `POST /recommendations/:id/downvote` | Score −1 (deleted below −5) |
| `GET /health` | Liveness probe (used by Render health checks) |
| `DELETE /tests/reset` | Truncate the table — **only registered when `MODE=TEST`** |

## Requirements

- Node.js 16+ (verified on Node 20)
- PostgreSQL 13+ running locally (or any `DATABASE_URL` you can reach)

## Running locally

### 1. Back-end

```bash
cd back-end
npm install
cp .env.example .env          # then edit DATABASE_URL if needed
npx prisma migrate deploy     # creates the recommendations table
npm run dev                   # http://localhost:5000
```

Required environment variables (see [`back-end/.env.example`](back-end/.env.example)):

| Variable | Meaning | Example |
| --- | --- | --- |
| `PORT` | Port the API listens on | `5000` |
| `DATABASE_URL` | PostgreSQL connection string used by Prisma | `postgres://postgres:postgres@localhost:5432/singmeasong` |
| `MODE` | Set to `TEST` to expose `DELETE /tests/reset` (tests only) | unset |

> ⚠️ Never commit real `.env` files — they are git-ignored; only the
> `.env.example` / `.env.test.example` templates belong in the repository.

### 2. Front-end

```bash
cd front-end
npm install
cp .env.example .env          # REACT_APP_API_BASE_URL=http://localhost:5000
npm start                     # http://localhost:3000
```

| Variable | Meaning | Example |
| --- | --- | --- |
| `REACT_APP_API_BASE_URL` | Base URL of the API (no trailing slash) | `http://localhost:5000` |

## Tests

```bash
cd back-end
cp .env.test.example .env.test   # separate database — tests truncate tables!
npm test                         # resets the test DB, runs unit + integration
npm run test:unit                # unit tests only
npm run test:integration         # integration tests only
```

All 26 back-end tests (12 integration + 14 unit) pass. The front-end also ships
Cypress E2E specs (`front-end/cypress/`) that expect the front-end on
`localhost:3000` and the back-end started with `npm run dev:test` (test mode).

## Deployment

### Front-end — GitHub Pages (live)

The production build is published from the
[`singmeasong-731-deploy`](https://github.com/ManuDiasCruz/singmeasong-731-deploy)
repository at <https://manudiascruz.github.io/singmeasong-731-deploy/>.
To redeploy after changes:

```bash
cd front-end
PUBLIC_URL=https://manudiascruz.github.io/singmeasong-731-deploy \
REACT_APP_API_BASE_URL=https://singmeasong-api-731.onrender.com \
npm run build
# copy build/ into the singmeasong-731-deploy repo (duplicate index.html as 404.html) and push
```

### Back-end — Render blueprint

[`render.yaml`](render.yaml) provisions everything the API needs (web service
`singmeasong-api-731` + free PostgreSQL). From the
[Render dashboard](https://dashboard.render.com/blueprints) choose **New
Blueprint Instance**, point it at this repository and branch, and apply — the
`DATABASE_URL` is wired automatically, migrations run on every deploy, and
`/health` is used as the health check. The live front-end is already built
against `https://singmeasong-api-731.onrender.com`, so once the blueprint is
applied the public app is fully functional.

## Fixes and improvements

All fixes are intentionally minimal — no architectural rewrites.

1. **Back-end crashed at startup** — `testController.ts` and `testService.ts`
   imported local modules without the `.js` extension, which Node ESM
   resolution rejects. Extensions added.
2. **`npm run dev` broken on modern Node** — nodemon invoked `ts-node` directly,
   which cannot load `.ts` ESM files on Node 20. The dev scripts now run
   `node --loader ts-node/esm` (and `ts-node` was bumped to 10.9.x for Node 20
   loader-API support).
3. **`npm start`/build broken** — there was no `build` script and `start`
   pointed at `dist/index.js`, which never existed. Added `build: tsc`, fixed
   `start` to `dist/server.js`, and scoped `tsconfig.json` to `src/` so `dist/`
   has a flat layout.
4. **Test suite could not run** — the factory called
   `require("random-youtube-music-video")`: `require` doesn't exist in ESM and
   the package isn't in `package.json`. Replaced with faker-generated YouTube
   URLs. Also fixed `NODE_OPTIONS=...` inline env (fails on Windows) with
   `cross-env`, and `prisma migrate reset` now gets `--force` so it runs
   non-interactively.
5. **Two broken tests** — the list test asserted an impossible ordering
   (API returns newest-first), and the top-recommendations test read `body.id`
   from a `201` response that has no body. Both now assert real behaviour.
6. **Truncated front-end `.env.example`** — shipped as
   `REACT_APP_API_BASE_URL=http://`, breaking every API call for anyone who
   copied it. Fixed, and back-end `.env.example` / `.env.test.example` added.
7. **Front-end hung on “Loading...” forever** when the API was unreachable —
   Home, Top and Random now surface a clear error message.
8. **Sub-path deployments broke routing** — `BrowserRouter` now derives its
   `basename` from `PUBLIC_URL` (empty, path or full URL).
9. **Stray dependency** — `react-player` (a React library) removed from the
   back-end's dependencies.
10. **Deployment added** — Render blueprint (`render.yaml`), `/health`
    endpoint, and the GitHub Pages front-end deployment described above.

## Known limitations / future improvements

- **The Render API service must be created once by the repository owner** (this
  environment has no Render credentials). Until the blueprint is applied, the
  live front-end shows "Could not load recommendations" — by design.
- Prisma 3 / Express 4 / CRA 5 are dated; upgrading (especially Prisma) is the
  highest-value modernization.
- `cors()` is wide open; restricting it to known origins would be safer.
- The random/top Cypress E2E specs still assume `localhost:3000`; they could
  read a `CYPRESS_BASE_URL` instead.
- Recommendation names allow any string; trimming/length limits would improve
  data quality.
