import app from "./app.js";
import express from "express";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { prisma } from "./database.js";

async function start() {
  if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required.");
  const port = Number(process.env.PORT || 5000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error("Invalid PORT.");
  if (process.env.NODE_ENV === "production") {
    const build = fileURLToPath(new URL("../../front-end/build/", import.meta.url));
    if (!existsSync(`${build}/index.html`)) throw new Error("Build the frontend before production startup.");
    app.use(express.static(build));
    app.get(["/", "/top", "/random"], (_req, res) => res.sendFile(`${build}/index.html`));
  }
  await prisma.$connect();
  const server = app.listen(port, "0.0.0.0", () => console.log(`Server is listening on port ${port}.`));
  server.on("error", () => { console.error("HTTP server failed to start."); process.exit(1); });
  const shutdown = () => {
    const timeout = setTimeout(() => process.exit(1), 10000);
    timeout.unref();
    server.close(() => { void prisma.$disconnect().finally(() => process.exit(0)); });
  };
  process.once("SIGTERM", shutdown);
  process.once("SIGINT", shutdown);
}

start().catch(() => {
  // Never print connection URLs or credential-bearing Prisma errors.
  console.error("Startup failed. Check DATABASE_URL, PORT, migrations, and the production build.");
  process.exit(1);
});
