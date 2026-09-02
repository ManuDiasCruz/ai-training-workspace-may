
import cors from "cors";
import express from "express";
import "express-async-errors";
import { existsSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";
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
app.use(express.json());

app.get("/health", async (req, res) => {
  await prisma.$queryRaw`SELECT 1`;
  res.status(200).send({ status: "ok", database: "connected" });
});

app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendBuildDirectory = path.resolve(
  currentDirectory,
  "../../front-end/build"
);

if (process.env.NODE_ENV === "production" && existsSync(frontendBuildDirectory)) {
  app.use(express.static(frontendBuildDirectory));
  app.get("*", (req, res) => {
    res.sendFile(path.join(frontendBuildDirectory, "index.html"));
  });
}

app.use(errorHandlerMiddleware);

export default app;
