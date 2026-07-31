import { faker } from "@faker-js/faker";

let sequence = 0;

// Matches the joi pattern the API enforces on youtubeLink. The counter keeps
// the name column (UNIQUE) from colliding across a run.
export function createRecommendation() {
  sequence += 1;

  return {
    name: `${faker.name.findName()} #${sequence}`,
    youtubeLink: `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`,
  };
}

// The link is deliberately not a YouTube URL, so POST /recommendations
// answers 422.
export function createWrongLink() {
  sequence += 1;

  const name = `${faker.name.findName()} #${sequence}`;

  return { name, youtubeLink: name };
}
