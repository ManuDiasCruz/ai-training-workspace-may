
import cors from "cors";
import express from "express";
import "express-async-errors";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { prisma } from "./database.js";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();
const allowedOrigins = process.env.CORS_ORIGIN
  ?.split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(cors(allowedOrigins?.length ? { origin: allowedOrigins } : undefined));
app.use(express.json({ limit: "10kb" }));

app.get("/health", async (_req, res) => {
  await prisma.$queryRaw`SELECT 1`;
  res.status(200).send({ status: "ok" });
});

app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  app.use("/tests", testsRouter);
}

if (process.env.SERVE_FRONTEND === "true") {
  const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
  const frontendBuildDirectory = path.resolve(
    currentDirectory,
    "../../front-end/build"
  );

  if (!fs.existsSync(frontendBuildDirectory)) {
    throw new Error(`Frontend build not found at ${frontendBuildDirectory}`);
  }

  app.use(express.static(frontendBuildDirectory));
  app.get("*", (_req, res) => {
    res.sendFile(path.join(frontendBuildDirectory, "index.html"));
  });
}

app.use((_req, res) => {
  res.status(404).send({ error: "Route not found" });
});

app.use(errorHandlerMiddleware);

export default app;
