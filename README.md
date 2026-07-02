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

This repo ships a **Render.com Blueprint** ([`render.yaml`](render.yaml)) that
provisions everything in one step:

1. Push this branch to GitHub (already done for `H2H-medium-sing`).
2. In Render: **New + → Blueprint**, connect this repository, and select the
   `H2H-medium-sing` branch.
3. Render creates:
   - a **free PostgreSQL** database,
   - the **API** web service (`buildCommand: npm install && npm run build`,
     `startCommand: npm run migrate:deploy && npm start`) with `DATABASE_URL`
     wired from the database automatically,
   - the **static SPA** built from `front-end/` with the SPA rewrite rule.
4. After the first deploy, set the front-end's `REACT_APP_API_BASE_URL` to the
   API service's public URL (e.g. `https://sing-me-a-song-api.onrender.com`) and
   redeploy the static site so the value is baked into the bundle.

Any equivalent host works: the API is a standard Node/Express service
(`npm run build` then `npm start`) and the front-end is a static CRA bundle
(`npm run build`, serve `front-end/build/`).

### Post-deploy verification checklist

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
8. **Added `render.yaml`** deployment blueprint and this README.

## ⚠️ Known limitations / future improvements

- **Live hosted deployment requires a hosting account.** The blueprint and build
  are verified locally; provisioning the live services needs the owner's
  Render (or equivalent) account. See the open GitHub issues for follow-ups.
- **Outdated dependencies.** Prisma 3.x, React 18 / CRA (deprecated), and a
  number of transitive packages report audit vulnerabilities. Upgrading is
  deliberately out of scope here to avoid an architectural rewrite.
- **No health-check / root route.** `GET /` returns 404; the deploy health check
  uses `/recommendations`. A dedicated `/health` endpoint would be cleaner.
- **Test suite not executed here** — it requires a live Postgres, which was not
  available in the repair environment. Scripts and env templates are provided.
