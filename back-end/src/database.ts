import * as prismaClientModule from "@prisma/client";

const prismaClientRuntime = prismaClientModule as any;
const PrismaClient =
  prismaClientRuntime.PrismaClient ?? prismaClientRuntime.default?.PrismaClient;

export const prisma = new PrismaClient();
