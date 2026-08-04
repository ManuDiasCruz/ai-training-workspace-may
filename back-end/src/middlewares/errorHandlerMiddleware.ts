import { Request, Response, NextFunction } from "express";
import prismaPackage from "@prisma/client";
import {
  AppError,
  errorTypeToStatusCode,
  isAppError
} from "../utils/errorUtils.js";

const { Prisma } = prismaPackage;

export function errorHandlerMiddleware(
  err: unknown,
  req: Request,
  res: Response,
  next: NextFunction
) {
  if (isAppError(err)) {
    return res.status(errorTypeToStatusCode(err.type)).send(err.message);
  }

  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    if (err.code === "P2002") return res.status(409).send("Recommendation already exists");
    if (err.code === "P2025") return res.sendStatus(404);
  }

  console.error(err);
  return res.sendStatus(500);
}
