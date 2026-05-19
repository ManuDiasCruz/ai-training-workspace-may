import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

export function createRandomSong(): Song {
  const slug = faker.random.alphaNumeric(11);
  const name = `${faker.name.findName()} ${faker.datatype.uuid()}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${slug}`;

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