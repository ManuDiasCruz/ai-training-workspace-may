import { faker } from "@faker-js/faker";

// "name" is UNIQUE in the database, so a counter keeps generated songs from
// colliding with each other inside a single spec run.
let songCounter = 0;

export function createRecommendation() {
  songCounter += 1;

  return {
    name: `${faker.music.songName()} - ${faker.name.findName()} #${songCounter}`,
    youtubeLink: `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`,
  };
}

export function createWrongLink() {
  songCounter += 1;

  return {
    name: `${faker.music.songName()} #${songCounter}`,
    youtubeLink: faker.lorem.word(),
  };
}
