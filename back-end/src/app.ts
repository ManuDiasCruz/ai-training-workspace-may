
import cors from "cors";
import express from "express";
import "express-async-errors";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";
import { prisma } from "./database.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();
const allowedOrigins = process.env.CORS_ORIGIN
  ?.split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(cors({ origin: allowedOrigins?.length ? allowedOrigins : true }));
app.use(express.json());

app.get("/health", async (_req, res) => {
  await prisma.$queryRaw`SELECT 1`;
  res.status(200).send({ status: "ok" });
});

app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

app.use(errorHandlerMiddleware);

export default app;
