import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

export function createRandomSong() {
  // Generate a deterministic, offline, unique song using faker only.
  // (The previous implementation used `require("random-youtube-music-video")`,
  // which is a CommonJS require in an ESM project and an undeclared dependency,
  // so the whole test suite failed to load.)
  const name = `${faker.music.songName()} - ${faker.name.findName()} (${faker.datatype.uuid()})`;
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
};

// export function createSong() {
//     const name = faker.name.findName();
//     const youtubeLink = `https://www.youtube.com/${faker.random.alphaNumeric(10)}`;    
    
//     return { name: name, youtubeLink: youtubeLink };
// };

export async function createRecommendation(song: Song) {
    return prisma.recommendation.create({ data: song });
};