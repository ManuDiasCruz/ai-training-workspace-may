import * as prismaPackage from "@prisma/client";

type PrismaModule = typeof import("@prisma/client");
const prismaModule = prismaPackage as PrismaModule & { default?: PrismaModule };
const PrismaClient = prismaModule.PrismaClient ?? prismaModule.default?.PrismaClient;

if (!PrismaClient) {
  throw new Error("PrismaClient is unavailable. Run `npx prisma generate` before starting the API.");
}

export const prisma = new PrismaClient();
