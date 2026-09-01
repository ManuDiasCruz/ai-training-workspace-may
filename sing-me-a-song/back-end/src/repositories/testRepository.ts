import { prisma } from "../database.js";

import { assertTestDatabase } from "../utils/testDatabase.js";

async function resetDatabase() {
    assertTestDatabase();
    return prisma.$transaction([
        prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`
    ]);
}

export const testRepository = {
    resetDatabase
}