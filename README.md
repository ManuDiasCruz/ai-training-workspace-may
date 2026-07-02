# 🎵 Sing Me a Song

A full-stack song-recommendation app. Users post YouTube song recommendations,
up/down-vote them, and browse them by **recency**, **top score**, or a
score-weighted **random** pick. Recommendations whose score drops below **-5**
are automatically removed.

> **About this branch (`H2H-medium-sing`)** — This branch imports the
> [`sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song) project into
> the workspace and repairs it into a runnable, documented, deployable state.
> The changes made are listed under [Fixes & improvements](#-fixes--improvements-made).
> (The workspace `main` branch hosts an unrelated static "Parrot Memory" game;
> that content is intentionally left untouched.)

## Stack

| Layer     | Technology                                                                        |
| --------- | --------------------------------------------------------------------------------- |
| Front-end | React 18 (Create React App), React Router 6, axios, styled-components, react-player |
| Back-end  | Node.js + Express (TypeScript, ESM), Prisma ORM                                   |
| Database  | PostgreSQL                                                                        |
| Tests     | Jest + Supertest (back-end), Cypress (front-end e2e)                              |

## Project structure

```text
.
├── back-end/               # Express + Prisma API
│   ├── prisma/
│   │   ├── schema.prisma    # Recommendation model
│   │   └── migrations/      # committed SQL migrations
│   ├── src/
│   │   ├── controllers/  routers/  services/  repositories/
│   │   ├── schemas/         # joi request validation
│   │   ├── middlewares/     # centralised error handler
│   │   ├── app.ts           # express app (exported for tests)
│   │   └── server.ts        # HTTP entry point -> compiles to dist/server.js
│   ├── .env.example         # required back-end env vars
│   └── .env.test.example    # env vars for the test suite
├── front-end/              # React single-page app
│   ├── src/
│   │   ├── components/  pages/  hooks/  services/
│   │   └── services/api.js  # axios instance (REACT_APP_API_BASE_URL)
│   └── .env.example
└── render.yaml             # one-click deployment blueprint (Render.com)
```

## API overview

| Method | Route                            | Description                                       |
| ------ | -------------------------------- | ------------------------------------------------- |
| POST   | `/recommendations`               | Create a recommendation (`name`, `youtubeLink`)   |
| GET    | `/recommendations`               | Latest 10 recommendations                         |
| GET    | `/recommendations/top/:amount`   | Top `:amount` by score                            |
| GET    | `/recommendations/random`        | Score-weighted random recommendation              |
| GET    | `/recommendations/:id`           | A single recommendation                           |
| POST   | `/recommendations/:id/upvote`    | +1 score                                          |
| POST   | `/recommendations/:id/downvote`  | -1 score (auto-deleted when score < -5)           |

`youtubeLink` must match a YouTube URL (`youtube.com` or `youtu.be`).

---

## Getting started (local development)

### Prerequisites

- **Node.js 18+** and npm
- A running **PostgreSQL** instance (local install, Docker, or a hosted DB)

### 1. Back-end

```bash
cd back-end
npm install
cp .env.example .env            # then edit DATABASE_URL to point at your Postgres
npx prisma migrate deploy       # apply migrations (creates the recommendations table)
npm run dev                     # dev server with hot reload (ts-node + nodemon) on :5000
```

For a production-style run:

```bash
npm run build                   # prisma generate + tsc -> dist/
npm start                       # node dist/server.js
```

### 2. Front-end

```bash
cd front-end
npm install
cp .env.example .env            # REACT_APP_API_BASE_URL defaults to http://localhost:5000
npm start                       # CRA dev server on :3000
```

Open http://localhost:3000.

### Required environment variables

**back-end/.env**

| Variable       | Required | Description                                                        |
| -------------- | -------- | ------------------------------------------------------------------ |
| `DATABASE_URL` | yes      | PostgreSQL connection string used by Prisma                        |
| `PORT`         | no       | API port (defaults to `5000`; hosts like Render inject their own)  |
| `MODE`         | no       | Set to `TEST` to expose the `/tests` reset router (e2e only)       |

**front-end/.env**

| Variable                  | Required | Description                                       |
| ------------------------- | -------- | ------------------------------------------------- |
| `REACT_APP_API_BASE_URL`  | yes      | Base URL of the back-end API (baked in at build)  |

> ⚠️ **Never commit real `.env` files.** Only the `.env.example` templates are
> tracked; `.gitignore` excludes every `.env*` except the examples.

### Running the tests

The test suite needs its **own** throwaway Postgres database (it is reset on every run):

```bash
cd back-end
cp .env.test.example .env.test  # point DATABASE_URL at a disposable DB
npm test                        # resets DB then runs unit + integration tests
```

Front-end e2e (requires both servers running and `MODE=TEST` on the API):

```bash
cd front-end
npx cypress open
```

---

## Deployment

The app has two deployable pieces: the **static front-end** (any static host)
and the **API + PostgreSQL** back-end (any Node host). Config files for the most
common hosts are included.

### Front-end (static host)

The production bundle is a plain static site (`front-end/build/`). Ready-to-use
configs are provided; all work with **private** repositories:

- **Netlify** — [`netlify.toml`](netlify.toml). *New site from Git* → pick this
  repo/branch; build settings and the SPA fallback are read from the file.
- **Vercel** — [`vercel.json`](vercel.json). *Import Project* → deploy.
- **Surge** (CLI): `cd front-end && PUBLIC_URL=/ npm run build && npx surge build`.
- **GitHub Pages**: `cd front-end && npm run deploy` publishes to the `gh-pages`
  branch (already done on this branch). ⚠️ Serving it requires a **public** repo
  or a paid plan — Pages is disabled for private repos on the free plan.

Set `REACT_APP_API_BASE_URL` (baked in at build time) to your API's public
origin before/at build. The included configs default it to the Render API URL
below; the SPA loads without the API but its data features need the API live.

### Back-end (API + database)

Ships a **Render.com Blueprint** ([`render.yaml`](render.yaml)): *New + →
Blueprint*, connect this repo/branch, and Render provisions a free PostgreSQL
DB and the API web service (`npm run build`, then
`npm run migrate:deploy && npm start`), wiring `DATABASE_URL` automatically.
Any Node host works — build with `npm run build` and start with `npm start`
(run `npm run migrate:deploy` first).

### Verification performed

- **Front-end build** verified served over HTTP and over a public HTTPS tunnel:
  `/` → `200` with the app shell, hashed JS/CSS assets → `200`, and the SPA
  fallback (`/random`) → `200`. Root-relative assets and the baked API URL confirmed.
- **Back-end build** verified to compile and boot (`Server is listening…`);
  `GET /recommendations` returns `200` once `DATABASE_URL` points at a live DB.

### Post-deploy checklist

- `GET https://<api-host>/recommendations` returns `200` with a JSON array.
- The SPA loads, and creating a recommendation makes it appear in the list.
- Up/down-vote buttons change the score; the **Top** and **Random** pages load.

---

## 🔧 Fixes & improvements made

The imported project compiled but **could not start in production** and had
broken setup defaults. The following minimal, targeted fixes were applied:

1. **Back-end crashed on startup (`ERR_MODULE_NOT_FOUND`).**
   `controllers/testController.ts` and `services/testService.ts` imported
   sibling modules without the `.js` extension that Node's ESM loader requires.
   Because `app.ts` imports that chain unconditionally, **every** compiled start
   failed. Added the missing extensions.
2. **`npm start` pointed at a non-existent file.** The start script ran
   `node dist/index.js`, but the entry point compiles to `dist/server.js`.
   Fixed `start` and `main`, and added a proper **`build`** script
   (`prisma generate && tsc`).
3. **TypeScript emitted to the wrong layout.** Without `rootDir`, `tsc` produced
   `dist/src/server.js` (and compiled the test folder). Set `rootDir: "src"`
   plus `include`/`exclude`, so the entry lands at `dist/server.js`.
4. **Front-end had a broken API URL.** `front-end/.env.example` shipped an
   incomplete `REACT_APP_API_BASE_URL=http://`, so a copied `.env` produced
   failed requests. Set a working local default and documented the production value.
5. **Missing environment documentation.** Added `back-end/.env.example` and
   `back-end/.env.test.example` documenting every required variable.
6. **Dangling Prisma seed config.** `package.json` referenced a non-existent
   `prisma/seed.ts`, which would break `prisma db seed` / non-skipped resets.
   Removed the dead config.
7. **Non-portable test script.** Replaced the inline `NODE_OPTIONS=...` (which
   fails on Windows shells) with the already-present `cross-env`.
8. **Deployment enablement.** Added `render.yaml` (back-end blueprint),
   `netlify.toml` + `vercel.json` (front-end static hosts), GitHub Pages
   support (`gh-pages` scripts, `homepage`, `404.html` fallback, Router
   `basename`), and this README.

## ⚠️ Known limitations / future improvements

- **Durable live hosting requires an account.** The front-end build is verified
  served publicly (local static server + public HTTPS tunnel), and the `gh-pages`
  branch is published — but GitHub Pages is disabled for this **private** repo on
  the free plan, and Netlify/Vercel/Surge/Render each need the owner's (free)
  account. Configs are provided so each is a one-step connect.
- **Back-end not yet live**, so the deployed front-end loads but its data
  features stay idle until the API is hosted (Render blueprint) and
  `REACT_APP_API_BASE_URL` is pointed at it.
- **Outdated dependencies.** Prisma 3.x, React 18 / CRA (deprecated), and a
  number of transitive packages report audit vulnerabilities. Upgrading is
  deliberately out of scope here to avoid an architectural rewrite.
- **No health-check / root route.** `GET /` returns 404; the deploy health check
  uses `/recommendations`. A dedicated `/health` endpoint would be cleaner.
- **Test suite not executed here** — it requires a live Postgres, which was not
  available in the repair environment. Scripts and env templates are provided.
