import {
  Song,
  createRandomSong,
  createRecommendation,
  createRecommendationWithScore
} from "./recommendationFactory.js";

// Every helper here used to be declared without `export`, so the whole module
// was unreachable dead code. The names also lied about what they did
// (createTwoSongsScenario inserted three rows) and createMoreThanTenScenario
// returned only the last song, discarding the rest.

export async function createSongWithNegativeScore(score = -5) {
  return createRecommendationWithScore(createRandomSong(), score);
}

export async function createManySongsScenario(numberOfPosts: number) {
  const songs: Song[] = [];

  for (let i = 0; i < numberOfPosts; i++) {
    const song = createRandomSong();
    await createRecommendation(song);
    songs.push(song);
  }

  return songs;
}

export async function createSongsWithScoresScenario(scores: number[]) {
  const songs: Song[] = [];

  for (const score of scores) {
    const song = createRandomSong();
    await createRecommendationWithScore(song, score);
    songs.push(song);
  }

  return songs;
}
