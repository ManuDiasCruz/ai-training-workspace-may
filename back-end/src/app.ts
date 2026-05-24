
import cors from "cors";
import express from "express";
import "express-async-errors";
import { errorHandlerMiddleware } from "./middlewares/errorHandlerMiddleware.js";

import testsRouter from "./routers/testRouter.js";
import recommendationRouter from "./routers/recommendationRouter.js";

const app = express();
const configuredOrigins = process.env.CORS_ORIGIN?.split(",").map((origin) =>
  origin.trim()
).filter(Boolean);

app.use(
  cors({
    origin:
      configuredOrigins && configuredOrigins.length > 0
        ? configuredOrigins
        : true,
  })
);
app.use(express.json());

app.get("/health", (req, res) => {
  res.status(200).send({ status: "ok" });
});

app.use("/recommendations", recommendationRouter);

if (process.env.MODE === "TEST") {
  console.log(" ***** RUNNING IN TEST MODE ***** ");
  app.use("/tests", testsRouter);
}

app.use(errorHandlerMiddleware);

export default app;
