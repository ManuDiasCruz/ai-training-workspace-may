import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

export function createRandomSong() {
  const name = faker.name.fullName();
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
};

export async function createRecommendation(song: Song) {
    return prisma.recommendation.create({ data: song });
};
