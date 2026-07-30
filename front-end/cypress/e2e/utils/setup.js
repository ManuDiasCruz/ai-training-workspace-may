import { faker } from "@faker-js/faker";

// Every spec imported this module, but it was never committed, so all three
// suites failed to compile before Cypress could run a single test.

let songCounter = 0;

// A recommendation whose youtubeLink satisfies the API's joi pattern, so
// POST /recommendations answers 201.
export function createRecommendation() {
  songCounter += 1;

  return {
    name: `${faker.name.findName()} #${songCounter}`,
    youtubeLink: "https://www.youtube.com/watch?v=qmUQr3zrqXM",
  };
}

// A recommendation whose youtubeLink is not a YouTube URL, so the API rejects
// it with 422.
export function createWrongLink() {
  songCounter += 1;

  const name = `${faker.name.findName()} #${songCounter}`;

  return { name, youtubeLink: name };
}
