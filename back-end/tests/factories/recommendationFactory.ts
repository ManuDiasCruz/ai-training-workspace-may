import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

let sequence = 0;

// Builds a song whose youtubeLink satisfies the joi pattern enforced by
// recommendationsSchemas.ts. The name carries a counter because the column is
// UNIQUE and faker repeats names often enough to make suites flaky.
export function createRandomSong(): Song {
  sequence += 1;

  const name = `${faker.name.findName()} #${sequence}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
};

export async function createRecommendation(song: Song) {
    return prisma.recommendation.create({ data: song });
};
