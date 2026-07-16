# 🎵 Sing Me a Song

A full-stack song-recommendation app. Users post YouTube song recommendations
and up-/down-vote them. Recommendations that drop below **-5** are removed
automatically. The app has three views:

- **Home** — add a recommendation and see the 10 most recent, newest first.
- **Top** — recommendations ranked by score.
- **Random** — a single random recommendation (weighted toward higher scores:
  70% of the time it picks from songs with score > 10 when any exist).

> This branch (`48-ehe-sing-me-a-song`) is a repaired and documented copy of
> the original project at
> [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song).
> See [Fixes & improvements](#-fixes--improvements-made) for what changed.

---

## 🧱 Tech stack

| Layer     | Technology                                                        |
| --------- | ----------------------------------------------------------------- |
| Front-end | React 18 (Create React App), React Router 6, styled-components, react-player, axios |
| Back-end  | Node.js + TypeScript (ESM), Express, Prisma ORM                    |
| Database  | PostgreSQL                                                         |
| Tests     | Jest + Supertest (back-end), Cypress (front-end e2e)              |

### Project structure

```text
.
├── back-end/            # Express + Prisma API
│   ├── prisma/          # schema + migrations
│   ├── src/             # routers → controllers → services → repositories
│   ├── tests/           # jest unit + integration tests
│   ├── Dockerfile
│   └── .env.example
├── front-end/           # React (Create React App) client
│   ├── src/
│   ├── cypress/         # e2e tests
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml   # run the whole stack locally
└── render.yaml          # one-click cloud deployment blueprint
```

### API reference

| Method | Route                            | Description                          |
| ------ | -------------------------------- | ------------------------------------ |
| POST   | `/recommendations`               | Create `{ name, youtubeLink }`       |
| GET    | `/recommendations`               | List the 10 most recent              |
| GET    | `/recommendations/top/:amount`   | Top N by score                       |
| GET    | `/recommendations/random`        | A random recommendation              |
| GET    | `/recommendations/:id`           | Get one by id                        |
| POST   | `/recommendations/:id/upvote`    | +1 score                             |
| POST   | `/recommendations/:id/downvote`  | -1 score (deletes if score < -5)     |

`youtubeLink` must match a YouTube URL (e.g. `https://www.youtube.com/watch?v=...`
or `https://youtu.be/...`).

---

## 🚀 Getting started (local development)

### Prerequisites

- **Node.js 18+** (tested on Node 20)
- **PostgreSQL 14+** running locally (or use Docker — see below)

### 1. Back-end

```bash
cd back-end
npm install

# Configure environment
cp .env.example .env
#   edit .env and set DATABASE_URL to your PostgreSQL instance

# Create the schema
npx prisma migrate deploy      # or: npx prisma migrate dev

# Run in watch mode
npm run dev                    # http://localhost:5000
```

### 2. Front-end

```bash
cd front-end
npm install

# Configure environment
cp .env.example .env
#   REACT_APP_API_BASE_URL should point at the back-end (default http://localhost:5000)

npm start                      # http://localhost:3000
```

Open <http://localhost:3000> — the front-end talks to the API on port 5000.

### Run everything with Docker (no local Node/Postgres needed)

```bash
docker compose up --build
# Front-end: http://localhost:3000   API: http://localhost:5000
```

---

## 🔐 Required environment variables

Secrets are **never committed** — `.env`, `.env.test` and `.env.local` are
git-ignored. Copy the provided `.env.example` files and fill them in.

### `back-end/.env`

| Variable       | Required | Example                                                             | Notes |
| -------------- | -------- | ------------------------------------------------------------------- | ----- |
| `DATABASE_URL` | ✅       | `postgresql://user:pass@localhost:5432/singmeasong?schema=public`   | Prisma connection string |
| `PORT`         | ❌       | `5000`                                                              | Defaults to 5000 |
| `MODE`         | ❌       | `TEST`                                                              | Set to `TEST` to expose the `/tests` helper routes used by e2e tests |

### `back-end/.env.test` (only needed to run the test suite)

Same keys as above, pointing at a **separate** test database (the suite
truncates/resets it). `MODE=TEST` is recommended.

### `front-end/.env`

| Variable                  | Required | Example                 | Notes |
| ------------------------- | -------- | ----------------------- | ----- |
| `REACT_APP_API_BASE_URL`  | ✅       | `http://localhost:5000` | Baked in at build time by Create React App |

---

## 🧪 Testing

### Back-end (Jest + Supertest)

Requires a **test database** and `back-end/.env.test`:

```bash
cd back-end
npm test                # resets the test DB, then runs unit + integration
npm run test:unit
npm run test:integration
```

All **26 tests pass**.

### Front-end (Cypress)

```bash
cd front-end
npx cypress open        # or: npx cypress run
```

The Cypress specs expect the API running with `MODE=TEST` (for the
`/tests/reset` route) and the front-end served at `http://localhost:3000`.

---

## ☁️ Deployment

### Option A — Render (recommended, full stack)

A [`render.yaml`](render.yaml) blueprint is included. It provisions a managed
PostgreSQL database, the API web service and the static front-end.

1. Push this branch to GitHub.
2. In Render: **New +** → **Blueprint** → select this repository.
3. Review the resources and **Apply**.
4. After the first deploy, set the web service's `REACT_APP_API_BASE_URL` to the
   API's public URL and redeploy (CRA bakes the URL in at build time).

### Option B — Docker anywhere

Both apps ship with a `Dockerfile`; `docker compose up --build` runs the whole
stack. Point any container host (Fly.io, a VPS, etc.) at these images.

### Option C — Split hosting

- **Front-end** is a static bundle (`npm run build` → `front-end/build`) and can
  be hosted on GitHub Pages, Netlify, Vercel, etc.
- **Back-end + PostgreSQL** can run on Render, Railway, Fly.io or a VPS.

> ⚠️ Whatever host you choose, set `REACT_APP_API_BASE_URL` (front-end, build
> time) to the deployed API URL, and `DATABASE_URL` (back-end) to the managed
> database. CORS is already open (`app.use(cors())`), so a cross-origin
> front-end works out of the box.

---

## 🛠 Fixes & improvements made

The project imported from the original repository did not run out of the box.
The following issues were diagnosed and fixed with minimal, targeted changes:

### Back-end
1. **Server crashed on boot — invalid ESM imports.** `testController.ts` and
   `testService.ts` used extensionless relative imports, which Node's native
   ESM rejects (`ERR_MODULE_NOT_FOUND`). Because `app.ts` loads the test router
   at module scope, this broke the entire app. Added the required `.js`
   extensions.
2. **`DATABASE_URL` not loaded.** The app never called `dotenv`, so Prisma threw
   `P1012 Environment variable not found: DATABASE_URL`. Added
   `import "dotenv/config"` at the entry point.
3. **No build step / wrong start entry.** `start` pointed at a non-existent
   `dist/index.js` and there was no `build` script. Added `build`
   (`prisma generate && tsc`), fixed `start`/`main` to `dist/server.js`, and set
   `rootDir`/`include` in `tsconfig.json` for a clean build output.
4. **Broken dev runner.** `npm run dev` failed (`ts-node` unresolved, and
   ts-node 10.7's ESM loader throws `ERR_LOADER_CHAIN_INCOMPLETE` on Node 18/20).
   Bumped ts-node to `^10.9.2` and added `nodemon.json` to run the ESM loader.
5. **Environment not documented.** Added `back-end/.env.example`.

### Tests
6. **Suite could not run.** The test factory used CommonJS `require()` in an ESM
   module (`require is not defined`) and depended on a network call. Replaced it
   with a deterministic faker-generated YouTube link. Fixed the `dotenv-cli`
   invocations (missing `--` swallowed flags), added `--force` to the
   non-interactive `prisma migrate reset`, and made the test script
   cross-platform with `cross-env`.
7. **Incorrect assertions.** The "List recommendations" test expected an
   impossible ordering; corrected it to match the API's `id desc` ordering.

### Front-end
8. **Incomplete API URL example.** `.env.example` shipped as `http://` with no
   host; set a usable `http://localhost:5000` default.
9. **Build warning.** Removed an unused `Component` import in `App.js`.

### Deployment
10. Added `Dockerfile`s, `docker-compose.yml` and `render.yaml`.

**Verification:** all 26 back-end tests pass; every API endpoint was exercised
with `curl`; and the full flow (create, list, upvote/downvote, top, random) was
verified in the browser against both the dev server and the **production build**
served statically — writes persist to PostgreSQL end-to-end.

---

## ⚠️ Known limitations & future improvements

- **No live public deployment in this branch.** A public back-end needs a
  managed host + database (Render/Railway/etc.). The configuration to do so is
  included (`render.yaml`, Docker), but provisioning it requires the repository
  owner's hosting account. Local + production-build integration was fully
  verified.
- **Dependencies are pinned to older majors** (Prisma 3.x, Express 4). Upgrading
  Prisma 3 → 6 and Express 4 → 5 would remove deprecation notices; do it
  deliberately with tests as a safety net.
- **`errorHandlerMiddleware` logs every error**, including expected 4xx
  (validation, not-found). Consider logging only unexpected 5xx.
- **Front-end has no error boundary / loading skeletons** beyond a bare
  "Loading..." string, and errors surface as `alert()` dialogs.
- **Cypress "advanced examples"** are the default CRA boilerplate and could be
  removed.

See the repository **Issues** (filtered by branch `48-ehe-sing-me-a-song`) for
tracked follow-ups.
