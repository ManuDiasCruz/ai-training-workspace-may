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

  console.error(err);

  if ("code" in err && err.code === "P2002") {
    return res.status(409).send("Recommendations names must be unique");
  }

  if ("code" in err && err.code === "P2025") {
    return res.sendStatus(404);
  }

  return res.sendStatus(500);
}
