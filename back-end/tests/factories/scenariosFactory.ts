import { prisma } from "../../src/database.js";

import { Song, createRandomSong, createRecommendation } from "./recommendationFactory.js"

async function createRandomSongPostWithNegativeScore(song: Song) {
    const newSong = await prisma.recommendation.create({
      data: { ...song, score: -5 },
    });
    return { ...newSong };
}
  
async function createTwoSongsScenario() {
    const songs: Song[] = [];
    for (let i = 0; i < 3; i++) {
      const isWrongLink = false;
      const newSong = createRandomSong();
      await createRecommendation(newSong);
      songs.push(newSong);
    }
    return songs;
}
  
async function createMoreThanTenScenario(numberOfPosts: number) {
    let song: Song;
    for (let i = 0; i < numberOfPosts; i++) {
      song = createRandomSong();
      await createRecommendation(song);
    }
    return song;
}
  
  async function createThreePostWithUpvotesScenario() {
    const upvotes = [14, 22, 31];
    for (let i = 0; i < upvotes.length; i++) {
      const newSong = createRandomSong();
      await prisma.recommendation.create({
        data: { ...newSong, score: upvotes[i] },
      });
    }
    return upvotes[1];
  }