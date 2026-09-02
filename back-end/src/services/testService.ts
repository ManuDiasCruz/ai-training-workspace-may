import { testRepository } from "../repositories/testRepository.js";
import { CreateRecommendationData } from "./recommendationsService.js";

async function deleteData() {
  return testRepository.resetDatabase();
}

/**
 * Creates `amount` recommendations. The first `highScorePercentage`% of them
 * receive a score above 10 (the threshold used by GET /recommendations/random),
 * the rest a score between 0 and 10. Only available when MODE=TEST.
 */
async function seedData(amount: number, highScorePercentage: number) {
  const highScoreCount = Math.round((amount * highScorePercentage) / 100);
  const suffix = Date.now().toString(36);

  const recommendations: (CreateRecommendationData & { score: number })[] = [];
  for (let i = 0; i < amount; i++) {
    const isHighScore = i < highScoreCount;
    recommendations.push({
      name: `Seed song ${i + 1} (${suffix})`,
      youtubeLink: `https://www.youtube.com/watch?v=${randomVideoId()}`,
      score: isHighScore
        ? 11 + Math.floor(Math.random() * 90)
        : Math.floor(Math.random() * 11),
    });
  }

  return testRepository.seed(recommendations);
}

function randomVideoId() {
  const alphabet =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  let id = "";
  for (let i = 0; i < 11; i++) {
    id += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return id;
}

export const testService = {
  deleteData,
  seedData,
};
