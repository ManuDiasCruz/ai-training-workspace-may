import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

// `name` is a unique column, so a bare faker name eventually collides once a
// scenario creates more than a handful of songs. The counter keeps generated
// songs distinct while leaving the rest of the value random.
let songCounter = 0;

export function createRandomSong(): Song {
  songCounter += 1;

  const name = `${faker.name.findName()} #${songCounter}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
};

export function createWrongLinkSong(): Song {
  songCounter += 1;

  return {
    name: `${faker.name.findName()} #${songCounter}`,
    youtubeLink: faker.lorem.words(3),
  };
};

export async function createRecommendation(song: Song) {
    return prisma.recommendation.create({ data: song });
};
