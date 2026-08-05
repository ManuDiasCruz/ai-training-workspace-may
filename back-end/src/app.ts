
import cors from "cors";
import express from "express";
import "express-async-errors";
import path from "path";
import { fileURLToPath } from "url";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();
const allowedOrigins = process.env.CORS_ORIGIN?.split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);
app.use(cors({ origin: allowedOrigins?.length ? allowedOrigins : false }));
app.use(express.json());

app.get("/health", (_req, res) => res.status(200).json({ status: "ok" }));
app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  app.use("/tests", testsRouter);
}

if (process.env.SERVE_FRONTEND === "true") {
  const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
  const frontendBuild = path.resolve(currentDirectory, "../../front-end/build");
  app.use(express.static(frontendBuild));
  app.get("*", (req, res, next) => {
    if (req.path.startsWith("/recommendations") || req.path.startsWith("/tests")) {
      return next();
    }
    return res.sendFile(path.join(frontendBuild, "index.html"));
  });
}

app.use((_req, res) => res.status(404).json({ error: "Route not found" }));
app.use(errorHandlerMiddleware);

export default app;
