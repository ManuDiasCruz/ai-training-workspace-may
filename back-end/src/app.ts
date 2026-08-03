
import cors from "cors";
import express from "express";
import "express-async-errors";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { prisma } from "./database.js";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();
const allowedOrigins = process.env.CORS_ORIGIN?.split(",").map((origin) =>
  origin.trim()
);

app.use(cors(allowedOrigins ? { origin: allowedOrigins } : undefined));
app.use(express.json());

app.get("/health", async (_req, res) => {
  await prisma.$queryRaw`SELECT 1`;
  res.status(200).json({ status: "ok" });
});

app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

const frontendBuild = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../front-end/build"
);

if (existsSync(frontendBuild)) {
  app.use(express.static(frontendBuild));
  app.get("*", (_req, res) => {
    res.sendFile(path.join(frontendBuild, "index.html"));
  });
}

app.use(errorHandlerMiddleware);

export default app;
