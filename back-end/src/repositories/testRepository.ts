import { prisma } from "../database.js";

async function resetDatabase() {
    return prisma.$transaction([
        prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`
    ]);
}

export const testRepository = {
    resetDatabase
}