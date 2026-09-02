import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

// "name" is UNIQUE in the database, so every generated song needs a name that
// cannot collide with a previous one inside the same run.
let songCounter = 0;

export function createRandomSong(): Song {
  songCounter += 1;

  const name = `${faker.music.songName()} - ${faker.name.findName()} #${songCounter}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
};

export function createWrongLinkSong(): Song {
  songCounter += 1;

  return {
    name: `${faker.music.songName()} #${songCounter}`,
    youtubeLink: faker.lorem.word(),
  };
};

export async function createRecommendation(song: Song) {
    return prisma.recommendation.create({ data: song });
};
