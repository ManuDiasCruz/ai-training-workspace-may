
import cors from "cors";
import express from "express";
import "express-async-errors";
import path from "path";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();
const corsOrigins = process.env.CORS_ORIGIN?.split(",")
  .map(origin => origin.trim())
  .filter(Boolean);

app.use(cors({ origin: corsOrigins?.length ? corsOrigins : true }));
app.use(express.json());

app.get("/health", (req, res) => res.sendStatus(200));
app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

if (process.env.NODE_ENV === "production") {
  const frontendBuildPath = path.resolve(process.cwd(), "../front-end/build");
  app.use(express.static(frontendBuildPath));
  app.get("*", (req, res) => {
    res.sendFile(path.join(frontendBuildPath, "index.html"));
  });
}

app.use(errorHandlerMiddleware);

export default app;
