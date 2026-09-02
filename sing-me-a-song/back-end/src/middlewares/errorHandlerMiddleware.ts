import { Request, Response, NextFunction } from "express";
import { errorTypeToStatusCode, isAppError } from "../utils/errorUtils.js";

export function errorHandlerMiddleware(err: any, _req: Request, res: Response, _next: NextFunction) {
  if (err?.type === "entity.parse.failed") return res.status(400).send("Invalid JSON");
  if (err?.type === "entity.too.large") return res.sendStatus(413);
  if (isAppError(err)) return res.status(errorTypeToStatusCode(err.type)).send(err.message);
  // Unique constraints and concurrent deletion must not turn into HTTP 500s.
  if (err?.code === "P2002") return res.status(409).send("Recommendations names must be unique");
  if (err?.code === "P2025") return res.sendStatus(404);
  if (["P1001", "P1002", "P1008", "P1017", "P2024"].includes(err?.code)) return res.sendStatus(503);
  // Avoid logging Prisma exception bodies, which may contain connection details.
  console.error("Request failed", { name: err?.name ?? "UnknownError", code: err?.code });
  return res.sendStatus(500);
}
