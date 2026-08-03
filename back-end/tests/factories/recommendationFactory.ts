import { prisma } from "../../src/database.js";

let recommendationSequence = 0;

export interface Song {
    name: string;
    youtubeLink: string;
};

export function createRandomSong() {
  recommendationSequence += 1;
  const suffix = `${Date.now()}-${recommendationSequence}`;
  const videoId = recommendationSequence.toString(36).padStart(11, "0");
  const name = `Test song ${suffix}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${videoId}`;

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
