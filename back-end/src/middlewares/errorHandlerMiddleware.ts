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
  console.error(err);

  if (isAppError(err)) {
    return res.status(errorTypeToStatusCode(err.type)).send({
      error: err.type,
      message: err.message,
    });
  }

  return res.status(500).send({
    error: "internal_server_error",
    message: "An unexpected error occurred",
  });
}
