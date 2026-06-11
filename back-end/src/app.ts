
import cors, { CorsOptions } from "cors";
import express from "express";
import "express-async-errors";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();
const allowedOrigins = process.env.CORS_ORIGIN
  ?.split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);
const corsOptions: CorsOptions = allowedOrigins?.length
  ? { origin: allowedOrigins }
  : {};

app.use(cors(corsOptions));
app.use(express.json());

app.get("/health", (_req, res) => res.send({ status: "ok" }));

app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

app.use(errorHandlerMiddleware);

export default app;
