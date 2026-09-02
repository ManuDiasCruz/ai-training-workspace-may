import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

export function createRandomSong() {
  const name = `Song ${faker.datatype.uuid()}`;
  const youtubeLink = "https://www.youtube.com/watch?v=qmUQr3zrqXM";

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
