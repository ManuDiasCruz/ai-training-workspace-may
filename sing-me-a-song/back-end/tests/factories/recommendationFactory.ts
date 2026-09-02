import { randomUUID } from "node:crypto";
import { prisma } from "../../src/database.js";
export interface Song { name: string; youtubeLink: string; }
export function createRandomSong(): Song {
  return { name: `Test song ${randomUUID()}`, youtubeLink: "https://www.youtube.com/watch?v=dQw4w9WgXcQ" };
}
export async function createRecommendation(song: Song) {
  return prisma.recommendation.create({ data: song });
}
