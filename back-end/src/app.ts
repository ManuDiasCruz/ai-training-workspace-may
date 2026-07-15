
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import cors from "cors";
import express from "express";
import "express-async-errors";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();

const allowedOrigins = process.env.CORS_ORIGIN?.split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(
  cors({
    origin: allowedOrigins?.length ? allowedOrigins : true,
  })
);
app.use(express.json());

app.get("/health", (_req, res) => {
  res.status(200).send({ status: "ok" });
});

app.use("/recommendations", recommendationRouter);

if (process.env.NODE_ENV === "test" || process.env.MODE === "TEST") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendDirectory = process.env.FRONTEND_DIST_PATH
  ? path.resolve(process.env.FRONTEND_DIST_PATH)
  : path.resolve(currentDirectory, "../../front-end/build");
const frontendIndex = path.join(frontendDirectory, "index.html");

if (existsSync(frontendIndex)) {
  app.use(express.static(frontendDirectory));
  app.get("*", (req, res, next) => {
    const isApiPath = ["/health", "/recommendations", "/tests"].some(
      (prefix) => req.path === prefix || req.path.startsWith(`${prefix}/`)
    );

    if (isApiPath || !req.accepts("html")) return next();
    return res.sendFile(frontendIndex);
  });
}

app.use((_req, res) => {
  res.status(404).send({ error: "Route not found" });
});

app.use(errorHandlerMiddleware);

export default app;
