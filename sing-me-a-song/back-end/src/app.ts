import "dotenv/config";
import cors from "cors";
import express from "express";
import "express-async-errors";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { prisma } from "./database.js";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";
import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";
import { assertTestDatabase } from "./utils/testDatabase.js";

const app = express();
app.disable("x-powered-by");
const origins = (process.env.CORS_ORIGINS ?? "http://localhost:3000")
  .split(",").map(origin => origin.trim()).filter(Boolean);
app.use(cors({ origin: origins }));
app.use(express.json({ limit: "16kb" }));

app.get("/health", async (_req, res) => {
  try {
    await prisma.recommendation.count();
    res.json({ status: "ok" });
  } catch {
    res.status(503).json({ status: "unavailable" });
  }
});
app.use("/api/recommendations", recommendationRouter);
// Keep the original API paths for existing clients.
app.use("/recommendations", recommendationRouter);
if (process.env.ENABLE_TEST_ROUTES === "true") {
  assertTestDatabase();
  app.use("/tests", testsRouter);
}
app.use(["/api", "/recommendations", "/tests"], (_req, res) => res.sendStatus(404));

// Both src/ and dist/ resolve to the same frontend build location.
const frontend = fileURLToPath(new URL("../../front-end/build/", import.meta.url));
if (existsSync(frontend + "index.html")) {
  app.use(express.static(frontend));
  app.get(["/", "/top", "/random"], (_req, res) => res.sendFile(frontend + "index.html"));
}
app.use(errorHandlerMiddleware);
export default app;
