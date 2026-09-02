import { testRepository } from "../repositories/testRepository.js";

async function deleteData(){
    return testRepository.resetDatabase();
}

// Bulk-seeds recommendations for the end-to-end suite. Scores cannot be set
// through the public API (POST always starts at 0 and votes move it by 1), so
// the Cypress "top" and "random" scenarios need this shortcut.
async function seed(amount: number, highScorePercentage: number) {
    const highScoreCount = Math.round((amount * highScorePercentage) / 100);

    const recommendations = Array.from({ length: amount }, (_, index) => ({
        name: `seeded song ${index + 1} - ${Date.now()}`,
        youtubeLink: `https://www.youtube.com/watch?v=seed${index + 1}`,
        // getRandom() splits the catalogue on "score > 10", so high-score songs
        // must land strictly above 10 and the rest at or below it.
        score: index < highScoreCount ? 11 + (highScoreCount - index) : index % 11,
    }));

    return testRepository.seedRecommendations(recommendations);
}

export const testService = {
    deleteData,
    seed
}
