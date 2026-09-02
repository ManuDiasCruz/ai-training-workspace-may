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

  const databaseError = err as Error & { code?: string; type?: string; status?: number };
  if (databaseError.code === "P2002") return res.status(409).send("Recommendations names must be unique");
  if (databaseError.code === "P2025") return res.sendStatus(404);
  if (databaseError.type === "entity.parse.failed") return res.status(400).send("Invalid JSON");
  if (databaseError.type === "entity.too.large") return res.sendStatus(413);
  console.error("Unhandled API error", { name: databaseError.name, code: databaseError.code });

  return res.sendStatus(500);
}
