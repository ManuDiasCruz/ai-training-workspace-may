import { Request, Response, NextFunction } from "express";
import {
  errorTypeToStatusCode,
  isAppError
} from "../utils/errorUtils.js";

export function errorHandlerMiddleware(
  err: unknown,
  _req: Request,
  res: Response,
  _next: NextFunction
) {
  if (isAppError(err)) {
    return res.status(errorTypeToStatusCode(err.type)).json({ error: err.message || err.type });
  }

  // A concurrent insert can race the service's friendly uniqueness check.
  if (hasPrismaCode(err, "P2002")) {
    return res.status(409).json({ error: "Recommendations names must be unique" });
  }
  if (hasPrismaCode(err, "P2025")) {
    return res.status(404).json({ error: "Recommendation not found" });
  }

  console.error("Unhandled application error", err);
  return res.status(500).json({ error: "Internal server error" });
}

function hasPrismaCode(error: unknown, code: string): boolean {
  return typeof error === "object" && error !== null &&
    (error as { code?: unknown }).code === code;
}
