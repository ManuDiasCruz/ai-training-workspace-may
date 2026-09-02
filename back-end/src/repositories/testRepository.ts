import { Prisma } from "@prisma/client";
import { prisma } from "../database.js";

async function resetDatabase() {
  return prisma.$transaction([
    prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`,
  ]);
}

async function seed(recommendations: Prisma.RecommendationCreateManyInput[]) {
  const result = await prisma.recommendation.createMany({
    data: recommendations,
  });
  return result.count;
}

export const testRepository = {
  resetDatabase,
  seed,
};
