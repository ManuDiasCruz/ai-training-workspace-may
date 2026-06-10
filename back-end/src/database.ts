import "dotenv/config";
import * as prismaClient from "@prisma/client";

const { PrismaClient } = (prismaClient as any).default ?? prismaClient;
export const prisma = new PrismaClient();
