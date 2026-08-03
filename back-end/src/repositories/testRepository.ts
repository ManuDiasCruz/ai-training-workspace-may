import { prisma } from "../database.js";

async function resetDatabase() {
    return prisma.$transaction([
        prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`
    ]);
}

export interface SeedOptions {
    amount: number;
    highScorePercentage: number;
}

// The Cypress "render screen" spec needs a populated database with a known mix
// of high and low scores. Doing that through the public API would take one POST
// plus a dozen upvotes per row, so it is inserted in a single statement here.
// Only reachable while MODE=TEST.
async function seedDatabase({ amount, highScorePercentage }: SeedOptions) {
    const highScoreCount = Math.round((amount * highScorePercentage) / 100);

    const data = Array.from({ length: amount }, (_, index) => ({
        name: `Seeded recommendation #${index + 1}`,
        youtubeLink: `https://www.youtube.com/watch?v=seed${index + 1}`,
        // recommendationsService.getScoreFilter splits the buckets at a score
        // of 10: "gt" for the popular ones, "lte" for everything else.
        score: index < highScoreCount ? 11 + index : index % 11
    }));

    await prisma.recommendation.createMany({ data });

    return { created: data.length, highScoreCount };
}

export const testRepository = {
    resetDatabase,
    seedDatabase
}
