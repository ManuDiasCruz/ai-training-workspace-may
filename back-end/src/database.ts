import dotenv from "dotenv";
import pkg from "@prisma/client";

// Loaded here so every entry point (server, tests) sees .env values before
// the Prisma client is created. Existing environment variables win.
dotenv.config();

const { PrismaClient } = pkg;
export const prisma = new PrismaClient();
