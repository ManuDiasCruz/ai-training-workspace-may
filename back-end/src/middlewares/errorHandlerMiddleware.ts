import { Request, Response, NextFunction } from "express";
import {
  AppError,
  errorTypeToStatusCode,
  isAppError
} from "../utils/errorUtils.js";

export function errorHandlerMiddleware(
  err: Error | AppError,
  _req: Request,
  res: Response,
  _next: NextFunction
) {
  if (isAppError(err)) {
    return res
      .status(errorTypeToStatusCode(err.type))
      .send({ error: err.message || "Request failed" });
  }

  console.error(err);
  return res.status(500).send({ error: "Internal server error" });
}
