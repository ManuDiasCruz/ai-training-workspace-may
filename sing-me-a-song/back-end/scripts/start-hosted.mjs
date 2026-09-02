import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { hostedDatabaseUrl } from "./hosted-database.mjs";

try {
  process.env.DATABASE_URL = hostedDatabaseUrl(process.env);
} catch (error) {
  console.error(error.message); // Validation messages contain no credentials.
  process.exit(1);
}

process.chdir(fileURLToPath(new URL("../", import.meta.url)));
const cli = fileURLToPath(new URL("../node_modules/prisma/build/index.js", import.meta.url));
const migration = spawnSync(process.execPath, [cli, "migrate", "deploy"], {
  env: process.env,
  stdio: "inherit",
});
if (migration.error || migration.status !== 0) {
  console.error("Hosted database migration failed; the server was not started.");
  process.exit(migration.status || 1);
}

// The server inherits the exact URL used for migrations and handles shutdown itself.
await import("../dist/server.js");
