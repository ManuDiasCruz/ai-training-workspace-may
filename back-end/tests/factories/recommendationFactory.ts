import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

export function createRandomSong() {
  const randomUrlGen = require("random-youtube-music-video");
  const youtubeUrl = randomUrlGen.getRandomMusicVideoUrl();

  const name = faker.name.findName();
  const youtubeLink = youtubeUrl;

  return { name, youtubeLink };
};

export async function createRecommendation(song: Song) {
    return prisma.recommendation.create({ data: song });
};