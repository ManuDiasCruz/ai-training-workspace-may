import { faker } from "@faker-js/faker";

// Three specs imported "./utils/setup.js", which did not exist in the
// repository, so they failed to compile before running a single assertion.

export function createRecommendation() {
  const name = `${faker.name.findName()} - ${faker.random.words(3)}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
}

export function createWrongLink() {
  const name = faker.name.findName();

  // Deliberately not a YouTube URL, so the API answers 422.
  return { name, youtubeLink: name };
}
