import { faker } from "@faker-js/faker";

// A fixed, valid recommendation.
export function createRecommendation() {
  const name = "Mundo Bita - O Circo chegou";
  const youtubeLink = "https://www.youtube.com/watch?v=qmUQr3zrqXM";

  return { name, youtubeLink };
}

// A random recommendation with a valid YouTube link.
export function createRandomSong() {
  const name = `${faker.music.songName()} - ${faker.name.findName()} ${faker.random.alphaNumeric(6)}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
}

// A recommendation whose link is NOT a YouTube URL (rejected with 422).
export function createWrongLink() {
  const name = faker.name.findName();
  const youtubeLink = name;

  return { name, youtubeLink };
}
