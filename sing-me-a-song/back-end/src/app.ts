
import "dotenv/config";
import cors from "cors";
import express from "express";
import "express-async-errors";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";
import { prisma } from "./database.js";

const app = express();
app.disable("x-powered-by");
app.use(cors({
  origin: (process.env.CORS_ORIGIN || "http://localhost:3000").split(",").map(origin => origin.trim()),
}));
app.use(express.json({ limit: "16kb" }));

app.get("/health", async (_req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    res.json({ status: "ok" });
  } catch {
    res.status(503).json({ status: "unavailable" });
  }
});

app.use("/recommendations", recommendationRouter);

if (process.env.NODE_ENV === "test" && process.env.ENABLE_TEST_ROUTES === "true") {
  if (!new URL(process.env.DATABASE_URL).pathname.endsWith("_test")) {
    throw new Error("Test routes require a dedicated database ending in _test.");
  }
  app.use("/tests", testsRouter);
}

// Unknown API paths must never fall through to the production SPA.
app.use("/recommendations", (_req, res) => res.sendStatus(404));
app.use("/tests", (_req, res) => res.sendStatus(404));

app.use(errorHandlerMiddleware);

export default app;
