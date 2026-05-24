# Sing Me a Song

A small full-stack web app for sharing and ranking YouTube music recommendations. The original code lives at [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song); this branch (`v2-mcc-task004/sing`) brings it back to a runnable state, fixes a handful of bugs, and documents the setup.

---

## Project overview

- **`back-end/`** — Node.js + TypeScript + Express + Prisma + PostgreSQL. Exposes a small REST API for creating recommendations, voting on them, listing top/random recommendations, and a test-only data reset endpoint.
- **`front-end/`** — React (Create React App) UI with three routes: Home (create + browse), Top (highest scored), and Random (weighted random pick). Talks to the back-end via Axios.

### API surface

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/recommendations` | Latest 10 recommendations (`id desc`). |
| `POST` | `/recommendations` | Create a recommendation (`name`, `youtubeLink`). |
| `GET` | `/recommendations/random` | Weighted random pick (70% score > 10, 30% ≤ 10). |
| `GET` | `/recommendations/top/:amount` | Top `:amount` by score. |
| `GET` | `/recommendations/:id` | Fetch a single recommendation. |
| `POST` | `/recommendations/:id/upvote` | +1 to score. |
| `POST` | `/recommendations/:id/downvote` | −1 to score; auto-delete when score < −5. |
| `DELETE` | `/tests/reset` | Truncate recommendations (only when `MODE=TEST`). |

---

## Required environment variables

Copy the example files and edit the values to match your local Postgres setup. **None of the real `.env` files are committed.**

### `back-end/.env`
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/singmeasong
PORT=5000
```

### `back-end/.env.test`
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/singmeasong_test
PORT=5001
MODE=TEST
```

### `front-end/.env`
```env
REACT_APP_API_BASE_URL=http://localhost:5000
```

`.env.example`, `.env.test.example`, and `front-end/.env.example` ship with placeholder values so anyone can bootstrap quickly.

---

## Setup (corrected)

Prerequisites: **Node 18+** (tested on Node 22), **npm 10+**, **PostgreSQL 14+**.

```bash
# 1. Provision databases (any user/password is fine; just match the URLs above)
sudo -u postgres psql -c "CREATE USER sing WITH PASSWORD 'sing' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE singmeasong OWNER sing;"
sudo -u postgres psql -c "CREATE DATABASE singmeasong_test OWNER sing;"

# 2. Back-end
cd back-end
cp .env.example .env             # then edit DATABASE_URL
cp .env.test.example .env.test   # then edit DATABASE_URL
npm install
npx prisma migrate deploy        # apply schema to dev DB
npx prisma generate
npm run dev                      # http://localhost:5000

# 3. Front-end (in a new shell)
cd front-end
cp .env.example .env
CYPRESS_INSTALL_BINARY=0 npm install --legacy-peer-deps
npm start                        # http://localhost:3000
```

Notes:
- `CYPRESS_INSTALL_BINARY=0` skips the Cypress binary download (CDN-restricted in many sandboxed environments). Drop it if you want to run the e2e tests locally.
- `--legacy-peer-deps` works around CRA 5's mismatched peer ranges on Node 22.

---

## Running tests

```bash
# Back-end unit + integration suite (resets the test DB before running)
cd back-end
npm run test

# Front-end (Cypress) — requires the binary to be installed
cd front-end
npx cypress open
```

All 26 back-end tests pass on Node 22 after the fixes in this branch.

---

## Deployment

Anything that can serve a static SPA + a Node process + Postgres works. A minimal recipe:

```bash
# Build the SPA
cd front-end && CI=true npm run build
# build/ is now ready for any static host (Netlify, Vercel, S3+CloudFront, Nginx, ...)

# Build and start the API
cd ../back-end
npm run build           # tsc -> dist/
npm start               # node dist/server.js (DATABASE_URL must be set in the host env)
```

For zero-config local verification, the repo also includes `npx serve -s front-end/build -l 3000` alongside `npm run dev` in `back-end/` — that's the combination used to validate this branch end-to-end.

Recommended hosting choices:
- **Front-end:** Vercel / Netlify (point at `front-end/`, build command `CI=true npm run build`, output `build`).
- **Back-end:** Render / Railway / Fly.io (use `npm run build && npm start`; expose `PORT`; set `DATABASE_URL` to a managed Postgres connection string).
- **Database:** any managed Postgres (Render, Supabase, Neon, RDS). After provisioning, run `npx prisma migrate deploy` once against the production URL.

Remember to set `REACT_APP_API_BASE_URL` to the deployed API URL **before** building the SPA, since CRA inlines env vars at build time.

---

## Fixes / improvements made on this branch

- **Back-end dev server crashed on Node 22.** Replaced `nodemon + ts-node` with `tsx watch`, which resolves `.js` import specifiers from `.ts` sources under ESM. Added a proper `build` script (`tsc`) and pointed `start` at `dist/server.js`.
- **Front-end build was failing under CI.** Removed an unused `Component` import from `App.js` that tripped `no-unused-vars` when CRA treats warnings as errors.
- **`.env.example` was unusable** (`REACT_APP_API_BASE_URL=http://`). Replaced with a working `http://localhost:5000` default and added matching `.env.example` / `.env.test.example` files for the back-end.
- **`prisma migrate reset` was failing non-interactively.** Added `--force` and the `dotenv -e .env.test --` separator so the flag is passed to Prisma, not consumed by dotenv-cli.
- **Test factory was unrunnable.** The `recommendationFactory` used `require("random-youtube-music-video")`, but the dep was never installed *and* CommonJS `require` is unavailable under the project's ESM config. Rewrote the factory to use Faker only.
- **Integration test had an incorrect ordering expectation.** `GET /recommendations` returns rows by `id desc`, so the list test now expects `[rec3, rec2, rec1]` instead of the original (impossible) `[rec2, rec1, rec3]`.
- **Documented required environment variables and added safe `.example` files** so secrets are never committed. The existing `back-end/.gitignore` already excludes `.env*` and now also keeps `.env.test.example` allowed.

---

## Known limitations / future improvements

- **Cypress e2e tests are skipped here.** The Cypress binary CDN is unreachable from the sandbox used to verify this branch. They are intended to work as-is once the binary downloads succeed.
- **`getRandom` distribution is fixed in code** (70/10 split, score threshold of 10). Worth making configurable.
- **`useRecommendation` on the Random page** re-fetches the *same* id after a vote instead of pulling a fresh random pick. UX could be improved with a "next" button that calls `/recommendations/random` again.
- **No CI workflow** — adding a GitHub Action that runs `npm run test` against a Postgres service container would catch regressions automatically.
- **Old transitive deps** still report a non-trivial vulnerability count via `npm audit`. CRA 5 and `prisma@3` are both EOL; a future task is upgrading to Vite + React 18 and Prisma 5.
- **No request validation tests for malformed YouTube URLs** beyond the 422 happy path. Edge cases (`youtu.be` shortcuts, trailing query strings) are accepted by the regex but not exercised.

---

## Original documentation

The upstream CRA-generated front-end README is preserved at [`front-end/README.md`](front-end/README.md).
