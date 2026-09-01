# Sing me a Song

A full-stack YouTube song-recommendation app. Add a song, browse the ten newest recommendations, vote, see the highest scores, or discover a random song. A recommendation is removed when its score falls below -5.

Imported from [ManuDiasCruz/sing-me-a-song](https://github.com/ManuDiasCruz/sing-me-a-song), source commit `46e4e117be89041aa1cc492558357d89ddb0306a`, into the `0827-beeh-singasong` branch of `ManuDiasCruz/ai-training-workspace-may`. This subdirectory is self-contained; unrelated target-repository files are unchanged. The original [frontend documentation](front-end/README.md) is retained.

## Structure and flow

| Location | Responsibility |
| --- | --- |
| `front-end/src` | React 18 UI, router, async hooks, Axios API client |
| `back-end/src/routers`, `controllers`, `services`, `repositories` | Express routes, validation, recommendation rules, Prisma queries |
| `back-end/prisma` | PostgreSQL schema and versioned migrations |
| `back-end/tests` | Jest unit tests and Supertest integration tests against a real test database |
| `front-end/cypress` | Browser end-to-end tests using the real API |
| `render.yaml` | One Node web service and one managed PostgreSQL database |

Development: React on port 3000 proxies API calls to Express on port 5000. Production: Express serves both the compiled frontend and the API on one origin, including direct navigation to `/top` and `/random`. No API URL or secret needs to be embedded in the production bundle.

## Requirements

- Node.js **22** (tested with 22.23.2), npm, and PostgreSQL **16**.
- Docker Compose is optional for local PostgreSQL. An existing PostgreSQL installation also works.
- Use the committed npm lockfiles. Do not run `npm audit fix --force`: the retained Create React App toolchain has incompatible major-upgrade suggestions.

## Setup

```sh
git clone --branch 0827-beeh-singasong https://github.com/ManuDiasCruz/ai-training-workspace-may.git
cd ai-training-workspace-may/sing-me-a-song
npm run setup
cp back-end/.env.example back-end/.env
cp back-end/.env.test.example back-end/.env.test
```

Edit the two backend environment files with your **separate** development and test database connection strings. Never point tests at an existing production database. The test database name must end in `_test`.

For Docker-based local databases:

```sh
cp .env.example .env
# Set a local POSTGRES_PASSWORD in .env and use the same password in the backend URLs.
docker compose up -d db
docker compose exec db createdb -U postgres sing_me_a_song_test
```

For an existing PostgreSQL server, create `sing_me_a_song` and `sing_me_a_song_test` with your PostgreSQL administration tool instead. If port 5432 is already occupied, use the existing server or change the Compose port and both connection strings.

Apply migrations, then start the API and frontend in separate terminals:

```sh
npm run db:migrate --prefix back-end
npm run dev --prefix back-end
```

```sh
npm start --prefix front-end
```

Open [localhost:3000](http://localhost:3000). No frontend `.env` is needed for the default proxy.

## Environment variables

| Variable | Where | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `back-end/.env`, `.env.test`, or hosting secret | PostgreSQL URL, including database name; required. Percent-encode special characters in credentials. Use the host's required TLS options for remote databases. |
| `PORT` | Backend / hosting | HTTP port; defaults to 5000. Hosting can supply its own value. |
| `NODE_ENV` | Backend / hosting | Set `production` for serving the compiled frontend; test scripts set `test`. |
| `CORS_ORIGIN` | Backend | Comma-separated allowed frontend origins for split hosting. Defaults to `http://localhost:3000`; same-origin production does not require an override. |
| `ENABLE_TEST_ROUTES` | Test runner only | Enables `/tests/reset` only with `NODE_ENV=test` and a `_test` database. Never set on a production service. The old `MODE=TEST` flag is intentionally unsupported. |
| `REACT_APP_API_BASE_URL` | Optional frontend build variable | Leave blank for the proxy/same-origin deployment. For separate hosting, use the API's full HTTPS origin and rebuild. This is public configuration, never a secret. |
| `POSTGRES_PASSWORD` | Root `.env` for Compose only | Your local database password, not used by the frontend. |
| `SMOKE_BASE_URL` | Smoke script | Application origin to verify; defaults to `http://localhost:5000`. |

Local `.env` files, logs, test videos, build output, and dependencies are ignored. Only placeholder examples are committed. Runtime errors do not print credential-bearing database exception messages. Do not paste credentials into issues, PRs, or email.

## Tests

```sh
npm test
npm run build
```

`npm test` runs backend unit/integration tests and frontend regression tests. Integration tests migrate and **erase only the dedicated `_test` database** between cases. They do not run `prisma migrate reset` or reset the development database. To run without PostgreSQL, use `npm run test:unit --prefix back-end` and `npm test --prefix front-end`.

End-to-end tests require the frontend on port 3000 and a test API on port 5000. Stop a development API already using port 5000, then run these in separate terminals:

```sh
npm run dev:test --prefix back-end
npm start --prefix front-end
npm run test:e2e --prefix front-end
```

Cypress uses `/tests/reset`, not the original broken `/reset` URL. Its active spec covers creation, voting, top/random navigation, validation, duplicate handling, removal, empty state, and outage/retry. The original tutorial and incomplete `.tests.js` files are retained for reference but excluded by the explicit `specPattern`.

If Cypress's first browser verification takes too long on Windows, set `$env:CYPRESS_VERIFY_TIMEOUT = '120000'` in PowerShell and retry. Do not skip browser verification.

The repository's dedicated GitHub Actions workflow runs tests, builds, browser flows, and a production smoke check with an ephemeral PostgreSQL service. See [verification notes](docs/verification.md) for observed results and the distinction between local and hosted verification.

## Production locally

```sh
npm run build
NODE_ENV=production npm run start:deploy
```

PowerShell equivalent:

```powershell
$env:NODE_ENV = 'production'
npm run start:deploy
```

`start:deploy` applies existing migrations before starting the compiled server. It never creates development migrations. `/health` returns 200 when the database is reachable and 503 otherwise. Missing configuration or missing frontend output causes a clear startup failure. Shutdown closes HTTP connections and disconnects Prisma.

On Windows, stop running API processes before `npm ci`, `prisma generate`, or rebuilding: Windows locks the loaded Prisma engine DLL. A rename/EPERM error for that DLL can be a running-process lock, not a database or application failure.

In another terminal, run `npm run test:smoke`. The smoke script creates a uniquely named recommendation, verifies API operations, and removes only that record through the normal downvote rule. It is a **mutating** check: use it only on an instance you own and intend to test.

## Deploy on Render

**Status: deployment configuration is ready; live deployment requires an authenticated hosting account. No hosted URL or successful remote verification is claimed.**

1. Sign in to Render and grant it access to the target GitHub repository.
2. Create a Blueprint from `ManuDiasCruz/ai-training-workspace-may`, select branch `0827-beeh-singasong`, and set the Blueprint file path to `sing-me-a-song/render.yaml`.
3. Review the proposed free web service and PostgreSQL database. Do not accept a paid plan without reviewing its cost. If names already belong to unrelated resources, choose unique names and update their reference together.
4. Render supplies `DATABASE_URL` from the managed database. Keep `NODE_ENV=production`; do not enable test routes. `CYPRESS_INSTALL_BINARY=0` skips the browser download during deployment, while `npm run setup` explicitly installs build dependencies even in production mode.
5. Wait for a successful build and healthy service. Open the actual URL returned by Render; verify creation, voting, Top, Random, and browser reloads. Verify `/tests/reset` returns 404.
6. Run the smoke check against that actual origin with `SMOKE_BASE_URL`, then record the deployment URL and results in `docs/verification.md` and the PR.

The free plan is for evaluation: web services can sleep and free PostgreSQL databases expire after 30 days. Arrange a durable database and backups before relying on saved recommendations. See [Render's free-tier limits](https://render.com/docs/free), [Node deployment guide](https://render.com/docs/deploy-node-express-app), and [Blueprint reference](https://render.com/docs/blueprint-spec).

Other Node/PostgreSQL hosts can use root directory `sing-me-a-song`, build command `npm run setup && npm run build`, and start command `npm run start:deploy`. Build and run on the same operating-system family so Prisma generates the correct native engine.

## API contract

| Endpoint | Result |
| --- | --- |
| `POST /recommendations` | `{name, youtubeLink}` → 201 with the created record; 409 for a duplicate name; 422 for invalid data |
| `GET /recommendations` | Ten newest records, newest first |
| `GET /recommendations/:id` | One record, or 404; malformed IDs return 422 |
| `POST /recommendations/:id/upvote` | Increment score; 200 or 404 |
| `POST /recommendations/:id/downvote` | Decrement; remove below -5; 200 or 404 |
| `GET /recommendations/top/:amount` | Highest scores with deterministic tie order; amount must be 1–100 |
| `GET /recommendations/random` | 70% preference for scores above 10, otherwise scores at most 10; fallback to all songs when a pool is empty; 404 when none exist |

Names are trimmed, nonempty, and at most 100 characters. YouTube links must be HTTP(S) video URLs with an eleven-character video ID; watch, short-link, shorts, and embed formats are supported. Validation checks URL shape, **not whether a video exists or is embeddable**. Invalid JSON returns 400 and bodies over 16 KiB return 413.

## Repairs and remaining work

- Fixed missing build/start wiring, ESM imports, environment loading, cross-platform test commands, missing test dependencies, and an invalid seed-script reference.
- Updated dependency lockfiles, patched Axios/Express/router dependencies, and kept React 18 and Create React App. Pinned frontend TypeScript 4.9.5 because CRA's optional peer otherwise selected an incompatible newer compiler. Updated Prisma and backend TypeScript/Jest for Node 22 and OpenSSL 3 without changing the database schema.
- Added same-origin production serving, database health, migration-before-start, graceful shutdown, and configurable development CORS.
- Added safe API validation, conflict handling under simultaneous creation, reliable score removal, deterministic ranking, and random eligibility beyond the newest ten songs.
- Fixed swallowed request failures, endless loading states, failed-save input loss, stale random records, and inaccessible vote/menu controls.
- Repaired test factories and assertions; added regression, browser, and production smoke checks.

Limitations: anonymous users can repeatedly vote or submit songs; add abuse controls/moderation before a public launch. Random selection currently reads its eligible pool into memory and should be optimized for large datasets. Third-party YouTube playback depends on availability, region, and embedding permissions. Legacy build/CLI dependency advisories remain a follow-up; audit summaries and scope are recorded in the verification notes. Hosting authentication and actual live verification remain outstanding.

Tracked follow-ups: [frontend tooling #538](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/538), [Prisma CLI advisories #539](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/539), [abuse controls #540](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/540), and [random-selection scaling #541](https://github.com/ManuDiasCruz/ai-training-workspace-may/issues/541).
