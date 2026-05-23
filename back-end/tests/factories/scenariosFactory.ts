import { prisma } from "../../src/database.js";
import { Song, createRandomSong, createRecommendation } from "./recommendationFactory.js";

export async function createRandomSongPostWithNegativeScore(song: Song) {
  return prisma.recommendation.create({ data: { ...song, score: -5 } });
}

export async function createThreeSongsScenario() {
  const songs: Song[] = [];
  for (let i = 0; i < 3; i += 1) {
    const newSong = createRandomSong();
    await createRecommendation(newSong);
    songs.push(newSong);
  }
  return songs;
}

export async function createMoreThanTenScenario(numberOfPosts: number) {
  let song: Song | null = null;
  for (let i = 0; i < numberOfPosts; i += 1) {
    song = createRandomSong();
    await createRecommendation(song);
  }
  return song;
}

export async function createThreePostsWithUpvotesScenario() {
  const upvotes = [14, 22, 31];
  for (const score of upvotes) {
    await prisma.recommendation.create({
      data: { ...createRandomSong(), score },
    });
  }
  return upvotes;
}
