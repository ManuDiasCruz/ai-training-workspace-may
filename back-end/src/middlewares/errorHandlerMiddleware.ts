import { Request, Response, NextFunction } from "express";
import {
  AppError,
  errorTypeToStatusCode,
  isAppError
} from "../utils/errorUtils.js";

export function errorHandlerMiddleware(
  err: Error | AppError,
  req: Request,
  res: Response,
  next: NextFunction
) {
  if (isAppError(err)) {
    return res.status(errorTypeToStatusCode(err.type)).send(err.message);
  }

  // Only genuinely unexpected failures are worth a stack trace; expected
  // domain errors (409/404/422) used to flood the logs on every bad request.
  console.error(err);

  return res.sendStatus(500);
}
