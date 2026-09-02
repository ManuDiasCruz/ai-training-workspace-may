import { prisma } from "../database.js";
import { Prisma } from "@prisma/client";

async function resetDatabase() {
    return prisma.$transaction([
        prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`
    ]);
}

async function seedRecommendations(
    recommendations: Prisma.RecommendationCreateManyInput[]
) {
    return prisma.recommendation.createMany({
        data: recommendations,
        skipDuplicates: true,
    });
}

export const testRepository = {
    resetDatabase,
    seedRecommendations
}
