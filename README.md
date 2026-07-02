# 🎵 Sing Me a Song

A full-stack song-recommendation app. Users post YouTube song recommendations,
up/down-vote them, and browse them by *recency*, *top score*, or a
score-weighted *random* pick. Recommendations that fall below **-5** points are
automatically removed.

> This branch (`H2H-low-sing`) imports the
> [`sing-me-a-song`](https://github.com/ManuDiasCruz/sing-me-a-song) project and
> repairs it into a runnable, documented state. See
> [Fixes & improvements](#fixes--improvements-made) below.

## Stack

| Layer     | Tech                                                            |
| --------- | -------------------------------------------------------------- |
| Front-end | React 18 (Create React App), React Router 6, axios, styled-components, react-player |
| Back-end  | Node.js + Express (TypeScript, ESM), Prisma ORM                |
| Database  | PostgreSQL                                                     |
| Tests     | Jest + Supertest (back-end), Cypress (front-end e2e)           |

## Project structure

```text
.
├── back-end/          # Express + Prisma API
│   ├── prisma/        # schema + migrations
│   └── src/
│       ├── controllers/  routers/  services/  repositories/
│       ├── schemas/       # joi validation
│       ├── middlewares/   # centralised error handler
│       ├── app.ts         # express app (exported for tests)
│       └── server.ts      # http entry point
└── front-end/         # React SPA
    └── src/
        ├── components/  pages/  hooks/  services/
```

## API overview

| Method | Route                          | Description                              |
| ------ | ------------------------------ | ---------------------------------------- |
| POST   | `/recommendations`             | Create a recommendation (`name`, `youtubeLink`) |
| GET    | `/recommendations`             | Latest 10 recommendations                |
| GET    | `/recommendations/top/:amount` | Top `:amount` by score                   |
| GET    | `/recommendations/random`      | Score-weighted random recommendation     |
| GET    | `/recommendations/:id`         | A single recommendation                  |
| POST   | `/recommendations/:id/upvote`  | +1 score                                 |
| POST   | `/recommendations/:id/downvote`| -1 score (auto-deleted below -5)         |

## Setup

### Prerequisites

- Node.js 16+ (tested on Node 20)
- A PostgreSQL database

### 1. Back-end

```bash
cd back-end
npm install
cp .env.example .env          # then edit DATABASE_URL
npx prisma migrate dev        # create tables
npm run dev                   # dev server (nodemon) on :5000
```

For production:

```bash
npm run build                 # prisma generate + tsc -> dist/
npm start                     # node dist/server.js
```

### 2. Front-end

```bash
cd front-end
npm install
cp .env.example .env          # point REACT_APP_API_BASE_URL at the API
npm start                     # dev server on :3000
npm run build                 # production static bundle -> build/
```

## Required environment variables

### `back-end/.env`

| Variable       | Required | Description                                              |
| -------------- | -------- | -------------------------------------------------------- |
| `DATABASE_URL` | yes      | PostgreSQL connection string used by Prisma              |
| `PORT`         | no       | API port (defaults to `5000`)                            |
| `MODE`         | no       | Set to `TEST` to expose the `/tests/reset` helper route  |

### `front-end/.env`

| Variable                  | Required | Description                                    |
| ------------------------- | -------- | ---------------------------------------------- |
| `REACT_APP_API_BASE_URL`  | yes      | Base URL of the back-end API (e.g. `http://localhost:5000`) |

> ⚠️ **Never commit real `.env` files.** They are git-ignored; only the
> `.env.example` templates are tracked.

## Deployment

The front-end and back-end deploy independently.

- **Front-end** — any static host. Run `npm run build` and serve the `build/`
  folder (Vercel, Netlify, GitHub Pages, `npx serve build`). Set
  `REACT_APP_API_BASE_URL` **at build time** to the deployed API URL.
- **Back-end** — any Node host with a PostgreSQL add-on (Render, Railway,
  Fly.io). Build command `npm run build`, start command `npm start`, and set
  `DATABASE_URL`. Run `npx prisma migrate deploy` on release to apply migrations.

See [Known limitations](#known-limitations--future-improvements) for the
current deployment status.

## Fixes & improvements made

- **Back-end failed to start under Node ESM** — `testController.ts` and
  `testService.ts` imported sibling modules without the required `.js`
  extension. Because `app.ts` statically imports the test router, this threw
  `ERR_MODULE_NOT_FOUND` and crashed the server on boot in every mode. Added the
  missing extensions.
- **Broken production/build scripts** — `start` pointed at a non-existent
  `dist/index.js` and there was no `build` script, so the app could not be
  compiled or run in production. Added `build` (`prisma generate && tsc`) and
  fixed `start` to `node dist/server.js` (and `main` accordingly).
- **Invalid front-end env template** — `front-end/.env.example` shipped the
  truncated value `REACT_APP_API_BASE_URL=http://`, which produced a broken
  axios base URL and made every request fail. Corrected to
  `http://localhost:5000`.
- **Missing back-end env template** — added `back-end/.env.example` documenting
  `DATABASE_URL`, `PORT`, and `MODE`.
- **Documentation** — added this project overview, setup, env-var, and
  deployment guide.

## Known limitations & future improvements

- **Database & live deployment** — the target environment had no PostgreSQL or
  Docker available, so the back-end could not be run end-to-end locally. The
  code is verified to type-check (`tsc --noEmit`) and the Prisma client
  generates cleanly; a full deploy needs a hosted Postgres instance.
- **No seed script** — `package.json` references `prisma/seed.ts`, which does
  not exist. Voting/browsing works but starts from an empty database.
- **No back-end input trimming / URL normalization** beyond the joi YouTube
  regex.
- **Front-end error UX** uses native `alert()` dialogs.

## Credits

Original project by
[@ManuDiasCruz](https://github.com/ManuDiasCruz/sing-me-a-song). This branch
repairs setup/runtime issues and adds documentation. The original
Create React App front-end notes are preserved in
[`front-end/README.md`](front-end/README.md).
