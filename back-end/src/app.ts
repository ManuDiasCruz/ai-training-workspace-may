
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
const allowedOrigins = (process.env.CORS_ORIGIN || "http://localhost:3000")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(cors({
  origin(origin, callback) {
    callback(null, !origin || allowedOrigins.includes(origin));
  },
}));
app.use(express.json());

app.get("/health", (_req, res) => res.status(200).json({ status: "ok" }));
app.get("/ready", async (_req, res) => {
  await prisma.$queryRaw`SELECT 1`;
  res.status(200).json({ status: "ready" });
});
app.use("/recommendations", recommendationRouter);
app.use("/recommendations", (_req, res) => res.sendStatus(404));

if (process.env.MODE === "TEST" && process.env.NODE_ENV !== "production") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

if (process.env.SERVE_FRONTEND === "true") {
  const buildPath = fileURLToPath(new URL("../../front-end/build", import.meta.url));
  if (existsSync(path.join(buildPath, "index.html"))) {
    app.use(express.static(buildPath));
    app.get("*", (_req, res) => res.sendFile(path.join(buildPath, "index.html")));
  } else {
    console.error(`Frontend build was not found at ${buildPath}`);
  }
}

app.use(errorHandlerMiddleware);

export default app;
