import { faker } from "@faker-js/faker";
import { prisma } from "../../src/database.js";

export interface Song {
    name: string;
    youtubeLink: string;
};

// Was `require("random-youtube-music-video")`, which fails twice over: `require`
// does not exist in an ES module, and the package was never declared in
// package.json. Generated locally instead - no network call, no extra
// dependency, and the link satisfies the regex in
// src/schemas/recommendationsSchemas.ts so factory POSTs are not 422s.
export function createRandomSong(): Song {
    const name = `${faker.name.findName()} - ${faker.random.words(3)}`;
    const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

    return { name, youtubeLink };
};

export function createSongWithInvalidLink(): Song {
    return { name: faker.name.findName(), youtubeLink: faker.random.word() };
};

export async function createRecommendation(song: Song) {
    return prisma.recommendation.create({ data: song });
};

export async function createRecommendationWithScore(song: Song, score: number) {
    return prisma.recommendation.create({ data: { ...song, score } });
};
